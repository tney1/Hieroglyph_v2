import json
import uuid
import hashlib
import logging
import asyncio
from os import getenv
import os
import io
import base64
from pathlib import Path
from fastapi_offline import FastAPIOffline
from fastapi.exceptions import HTTPException
from fastapi import Query
from fastapi import Depends, BackgroundTasks, Request, Body
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Any

from hieroglyph.pipeline import (process_ocr, validate_input_ocr_data,
                                validate_input_pipeline_data, validate_input_translate_data)
from hieroglyph.models import (PipelineRequestData, OCRRequestData, BatchPipelineRequestData, TranslateRequestData,
                              BulkTranslateRequestData, BatchPipelineStatusRequestData, PageStateModel, DBLoadAttrs, Inputb64)
from hieroglyph.translation.translator import Translator
from hieroglyph.translation import translate_page_data
from hieroglyph.utils.text import TextWrapper
from hieroglyph.general import INBOUND_IMAGE_TYPE
# from hieroglyph.boxes import find_table_rectangles
# Database Imports
import pymongo
import sqlalchemy
from sqlalchemy.orm import Session
from bson.json_util import dumps, loads, RELAXED_JSON_OPTIONS, CANONICAL_JSON_OPTIONS

from hieroglyph.db.mongo_db import _connect_to_mongo, _check_db_if_hash_already_exists
from hieroglyph.db import sqlite_crud, sqlite_models
import hieroglyph.db.sqlite_db as sqlite_db
from hieroglyph.ocr import TABLE_CONFIDENCE_THRESHOLD

from utils.image import ImageWrapper
from process.boxes import global_buffer_to_export
from fastapi import UploadFile, File
from PIL import Image


"""
from img2table.document import Image as img2table_Image  # no longer need since using our own table table extraction
from img2table.document import PDF
from img2table.ocr import TesseractOCR
"""

logger = logging.getLogger(__name__)
logger.debug("Creating database tables")
sqlite_db.Base.metadata.create_all(bind=sqlite_db.engine, checkfirst=True)
logger.debug(f"Database tables: {sqlite_db.Base.metadata.tables.keys()}")


app = FastAPIOffline(max_body_size = 104857600) # this is the max for Fast API (100MB)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_headers=['*'],
    allow_methods=['*']
)
translator = Translator()


def get_db():
    db = sqlite_db.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root_route():
    logger.info("API endpoint root('/') request received")
    return {"status": "GOOD"}


@app.get("/info")
def info_route():
    logger.info("API endpoint 'info' request received")
    return {"source_language": translator.source_language,
            "model_loaded": translator.model_loaded}


def _single_pipe_processing(input_image_data: PipelineRequestData):
    debug_mode = True if logger.getEffectiveLevel() == logging.DEBUG else False

    input_image_data = validate_input_pipeline_data(input_image_data)
    logging.info(f"API endpoint 'pipeline' request received for: {input_image_data.image_type.value}")

    output_image_data, image_to_transforms_map = process_ocr(input_image_data, debug=debug_mode or input_image_data.overlay.lower() == "true")
    logger.debug(f"Receive Image Type of {input_image_data.image_type.value} on /pipeline Endpoint")
    logger.debug(f"**Debugging all available output_image_data: {sum(len(boxes.data) for boxes in output_image_data)}")
    all_pages = []
    for page in output_image_data:
        data = translate_page_data(textwrapper=page, lang_in=input_image_data.src_lang,
                                   lang_out=input_image_data.dst_lang, translator=translator)
        page_dict = {
            'metadata': input_image_data.metadata,
            **data
        }

        # Get the page ImageWrapper from the image_to_transforms_map keys and map it to the page_dict TextWrapper
        #  so we can overlay text on the image
        if input_image_data.overlay.lower() == "true":  # Uses overlay flag
            if page_image := next((page for page in image_to_transforms_map.keys() if page.name == page_dict['name']), None):
                logger.debug(f"Overlaying image: {page_image.name}")
                overlay_data = page.overlay(page_image.get_array(), debug=debug_mode)
                page_dict['b64_overlay'] = overlay_data

        all_pages.append(page_dict)

    yield json.dumps(all_pages).encode()


@app.post("/pipeline")
def pipeline_route(input_image_data: PipelineRequestData):
    """
    Performs OCR and translation of provided inputs, accepts dict corresponding to an image with the format:
    {
        "name": "name of the image to ocr, inferring filetype here",
        "src_lang": "chinese", [OPTIONAL] default chinese
        "dst_lang": "english" [OPTIONAL] default english
        "b64data": "b64 encoded image bytes",
        "metadata": {} # Key value pairs of other metadata about the image
        "box_scale": 1 [OPTIONAL] scale for the boxes from 1-10 with 1 being bigger boxes and 10 being smaller boxes
        "density_scale": 1 [OPTIONAL] scale for the boxes from 1-10 with 1 being less dense boxes and 10 being more dense boxes
        "overlay": "False" [OPTIONAL] default False, triggers return of base64 overlay of image
        "conf_threshold": 50 [OPTIONAL] Scale 0-100 to sets the confidence threshold dynamically to adjust the tolerance level of OCR
    }
    Returns
    [{
        "name": "name of the image to ocr, inferring filetype here",
        "language": "language we recognized characters from when doing OCR"
        "data": [
            {
                "text": "",
                "translation": "",
                "bounding_box": [x, y, w, h], # x, y, width, height of text box
            }
        ]
        "metadata": {},
        "b64_overlay": "base64 overlay of image"  # IF DEBUG
    }]
    """
    # debug_mode = True if logger.getEffectiveLevel() == logging.DEBUG else False
    all_pages = _single_pipe_processing(input_image_data)
    return StreamingResponse(all_pages)


@app.post("/ocr")
def ocr_route(input_image_data: OCRRequestData):
    """
    Only OCRs with no translation of content performed, accepts dict corresponding to an image with the format:
    {
        "name": "name of the image to ocr, inferring filetype here",
        "src_lang": "chinese", [OPTIONAL] default chinese
        # "dst_lang": "english" [OPTIONAL] default english
        "b64data": "b64 encoded image bytes",
        "metadata": {} # Key value pairs of other metadata about the image
        "box_scale": 1 [OPTIONAL] scale for the boxes from 1-10 with 1 being bigger boxes and 10 being smaller boxes
        "density_scale": 1 [OPTIONAL] scale for the boxes from 1-10 with 1 being less dense boxes and 10 being more dense boxes
        "overlay": "False" [OPTIONAL] default False, triggers return of base64 overlay of image
        "conf_threshold": 50 [OPTIONAL] Scale 0-99 to sets the confidence threshold dynamically to adjust the tolerance level of OCR
    }
    Returns
    [{
        "name": "name of the image to ocr, inferring filetype here",
        # "language": "language we recognized characters from when doing OCR"
        "data": [
            {
                "text": "",
                "bounding_box": [x, y, w, h], # x, y, width, height of text box
            }
        ]
        "metadata": {},
    }]
    """
    debug_mode = True if logger.getEffectiveLevel() == logging.DEBUG else False
    input_image_data = validate_input_ocr_data(input_image_data)
    logging.info(f"API endpoint 'ocr' request received for: {input_image_data.image_type.value}")

    output_image_data, __ = process_ocr(input_image_data)  # Modified Process Diagram
    logger.debug(f"Receive Image Type of {input_image_data.image_type.value} on /ocr Endpoint")  # Update if 'image_type' is changed
    logger.debug(f"**Debugging all available output_image_data: {sum(len(boxes.data) for boxes in output_image_data)}")
    return [{"metadata": input_image_data.metadata, **page.to_dict()} for page in output_image_data]


@app.post("/translate")
def translate_route(input_translate_data: TranslateRequestData):
    """
    Translate, no preprocessing and no OCR. Accepts strings of text with the format:
    {
        "src_lang": "chinese", [OPTIONAL] default chinese
        "dst_lang": "english" [OPTIONAL] default english
        "text": "text to translate"
    }
    Returns
    {
        "result": "translated text, from src_lang to dst_lang",
    }
    """
    input_translate_data = validate_input_translate_data(input_translate_data)
    logging.info(f"API endpoint 'translate' request received")
    translate_response_list = translator.translate(lang_in=input_translate_data.src_lang,
                                                   lang_out=input_translate_data.dst_lang,
                                                   text=input_translate_data.text)

    return {"result": translate_response_list[0]}


@app.post("/bulk-translate")
def translate_route(input_translate_data: BulkTranslateRequestData):
    """
    Translate, no preprocessing and no OCR. Accepts strings of text with the format:
    {
        "translations": [
            {
                "text": "text to be translated",
                "src_lang": "chinese", default chinese
                "dst_lang": "english", default english
                "id": "id1",[OPTIONAL] identifier to associate with this translation
            }
        ]
    }
    Returns
    {
        "id1": "translated text, from src_lang to dst_lang",
        "id2": "translated text, from src_lang to dst_lang",
    }
    """
    all_results = {}
    logging.info(f"API endpoint 'bulk-translate' request received")
    for index, translate_request in enumerate(input_translate_data.translations):

        translate_request = validate_input_translate_data(translate_request)
        translate_response_list = translator.translate(lang_in=translate_request.src_lang,
                                                       lang_out=translate_request.dst_lang,
                                                       text=translate_request.text)
        if translate_request.id:
            all_results[translate_request.id] = translate_response_list[0]
        else:
            all_results[index] = translate_response_list[0]

    return all_results


@app.post("/batch-pipeline")
def batch_pipeline_route(batch_input_image_data: BatchPipelineRequestData,
                         background_tasks: BackgroundTasks,
                         db: Session = Depends(get_db)):
    """
    Performs OCR and translation of a list of provided inputs.
    Accepts a request containing a list of dicts each corresponding to an image with the following combined format:

    {
        "images": [
            {
                "name": "name of the image to ocr, inferring filetype here",
                "b64data": "b64 encoded image bytes",
                "src_lang": "chinese", [OPTIONAL] default chinese
                "dst_lang": "english" [OPTIONAL] default english
                "image_type": "text", default text
                "metadata": {} [OPTIONAL] Dict of key value pairs of other metadata about the image
                "box_scale": 1 [OPTIONAL] scale for the boxes from 1-10 with 1 being bigger boxes and 10 being smaller boxes
                "density_scale": 1 [OPTIONAL] scale for the boxes from 1-10 with 1 being less dense boxes and 10 being more dense boxes
                "overlay": "False" [OPTIONAL] default False, triggers return of base64 overlay of image
            },
            {
                # ... Subsequent Records Following the Pattern Above
            }
        ]
    }

    Returns JSON containing a list of the internal IDs and names logged into the database if successful, 400 if unsuccessful
    [
        {
            "internal_id": "1234-5678-..."
            "name": "{filename}"
        },
        {
            # ... Subsequent Records Following the Pattern Above
        }
    ]

    """
    logging.info(f"API endpoint 'batch-pipeline' request received")
    debug_mode = True if logger.getEffectiveLevel() == logging.DEBUG else False

    generated_jobs = []

    output_folder = Path(getenv("DATA_DIR", "/data/"))
    output_folder.mkdir(exist_ok=True, parents=True)

    for image_data in batch_input_image_data.images:

        logger.debug("Sending a job to the batch processing pipeline...")

        internal_id = uuid.uuid4()

        image_data.internal_id = str(internal_id)

        output_file = output_folder / f"{image_data.name}.json"

        new_batch_job = sqlite_crud.create_batch_job(
            db=db,
            name=image_data.name,
            dst_lang=image_data.dst_lang,
            image_type=image_data.image_type,
            running=False, failure=False, success=False, completed=False,
            internal_id=str(internal_id),
            output_location=str(output_file)
        )

        generated_jobs.append(
            {
                "name": new_batch_job.name,
                "internal_id": new_batch_job.internal_id
            }
        )
    logger.debug(f"Adding tasks for {generated_jobs}...")
    background_tasks.add_task(_background_job_processing, batch_input_image_data, output_folder, db)
    logger.debug("Jobs sent to background processing")
    return generated_jobs


def _background_job_processing(batch_input_image_data: BatchPipelineRequestData,
                               output_folder: Path, db: Session = Depends(get_db)):
    """
    batch_input_image_data:     {
        "images": [
            {
                "name": "name of the image to ocr, inferring filetype here",
                "b64data": "b64 encoded image bytes",
                "src_lang": "chinese", [OPTIONAL] default chinese
                "dst_lang": "english" [OPTIONAL] default english
                "image_type": "text", default text
                "metadata": {} [OPTIONAL] Dict of key value pairs of other metadata about the image
                "box_scale": 1 [OPTIONAL] scale for the boxes from 1-10 with 1 being bigger boxes and 10 being smaller boxes
                "density_scale": 1 [OPTIONAL] scale for the boxes from 1-10 with 1 being less dense boxes and 10 being more dense boxes
                "overlay": "False" [OPTIONAL] default False, triggers return of base64 overlay of image
            }
        ]
    }
    output_folder: Folder for data output
    db: Session
    """
    all_processed_image_data = []  # Where Translations from All Pages Dump
    debug_mode = True if logger.getEffectiveLevel() == logging.DEBUG else False

    for image_data in batch_input_image_data.images:

        try:
            image_data = validate_input_pipeline_data(image_data)

            # Marks Job as Running and Pending a Failure/Success/Completed Decision
            logger.debug(f"Marking job with UUID {image_data.internal_id} as running...")
            sqlite_crud.update_job_status_flags(
                db=db, internal_id=image_data.internal_id,
                running=True, failure=False, success=False, completed=False)

            logger.debug(f"Retrieving expected output location...")
            location_query = sqlite_crud.get_batch_job_by_internal_id_non_serialized(db=db, internal_id=image_data.internal_id)
            output_location = location_query.output_location

            logger.debug(f"Processing: {image_data}")
            output_image_data, image_to_transforms_map = process_ocr(image_data, debug=debug_mode or image_data.overlay.lower() == "true")
            logger.debug(f"Received Image Type of {image_data.image_type.value} on /batch-pipeline Endpoint")

            logger.debug(f"**Debugging all available output_image_data: {sum(len(boxes.data) for boxes in output_image_data)}")
            all_pages = []
            for page in output_image_data:
                data = translate_page_data(textwrapper=page, lang_in=image_data.src_lang,
                                           lang_out=image_data.dst_lang, translator=translator)
                page_dict = {
                    'metadata': image_data.metadata,
                    **data
                }
                if image_data.overlay.lower() == "true":
                    # Get the page ImageWrapper from the image_to_transforms_map keys and map it to
                    #  the page_dict TextWrapper so we can overlay text on the image
                    if page_image := next((page for page in image_to_transforms_map.keys() if page.name == page_dict['name']), None):
                        logger.debug(f"Overlaying image: {page_image.name}")
                        page_dict['b64_overlay'] = page.overlay(page_image.get_array(), debug=debug_mode)
                all_pages.append(page_dict)
            all_processed_image_data.extend(all_pages)

            json_output_name = output_folder / (f"{image_data.name}.json")
            logger.debug(f"Preparing to write JSON data to {json_output_name}...")

            with open(json_output_name, 'w+') as f:
                json.dump(all_pages, f)

            logger.debug(f"Completed writing file to {output_folder} directory.")

            # Marks Job as Successfully Completed
            logger.debug(f"Marking job with UUID {image_data.internal_id} as complete...")
            sqlite_crud.update_job_status_flags(
                db=db, internal_id=image_data.internal_id,
                running=False, failure=False, success=True, completed=True)

        except Exception as e:

            logger.error(f"Error encountered, marking current job with UUID {image_data.internal_id} as failed. See error: {e}")

            # Marks Job as Failed and Exited
            sqlite_crud.update_job_status_flags(
                db=db, internal_id=image_data.internal_id,
                running=False, failure=True, success=False, completed=True)
            pass  # Continue to Next Entry

    logger.debug(f"All background jobs have been processed. Check status using the /batch-status API endpoint.")

    # return all_processed_image_data


@app.post("/batch-status")
def batch_status_route(status_request: BatchPipelineStatusRequestData, db: Session = Depends(get_db)):
    """
    If a single ID is provided, returns the status of a specific job. If the status of the specific job is complete,
    the full base64 of the output file will be provided to the user. Otherwise, if no ID is provided the endpoint will
    simply return the status of all batch jobs in the database with no base64 included.

    I.e., Accepts empty request without paramaters or optionally:

    {
        "internal_id": "12345678-1234-5678-1234-567812345678"
    }

    Return:
        {
            "name": output_value,
            "internal_id": uuid_value,
            "data": data
        }
    OR
        {
            "name": output_value,
            "internal_id": uuid_value,
            "success": str(success_value),
            "failure": str(failure_value),
            "completed": str(completed_value)
        }

    """
    logging.info(f"API endpoint 'batch-status' request received")
    internal_id = status_request.internal_id

    if internal_id:
        logger.debug(f"Request contained an internal ID, searching and returning record for the following entry: {internal_id}")
        job_record = sqlite_crud.get_batch_job_by_internal_id(db=db, internal_id=internal_id)
        return _check_output_and_return_b64(job_record)
    else:
        logger.debug("Request did not contain an internal ID, returning all records in the database...")
        all_jobs = sqlite_crud.get_all_batch_jobs(db=db)
        return [_get_job_data(job_record) for job_record in all_jobs]


@app.post("/save-session")
def save_session_db_route(page_state: PageStateModel):
    """
    Saves UI data into a given MongoDB container to cache session information

    :param page_state: JSON containing Page UI data
    :returns: List of ObjectIDs for Created Records in Mongo (One Per Page)
    """
    logging.info(f"API endpoint 'save-session' request received")
    logger.debug(f"Received: \n{page_state}\n")
    data = json.loads(page_state.json())

    data_hash = data["hash"]  # Key with SHA-256 Hash from Frontend

    column_target = _connect_to_mongo()

    if _check_db_if_hash_already_exists(data_hash):
        logger.info("Passed hash already exists in the database. Deleting existing entries...")

        # Overwrites Documents with Same Hash
        query = {"src_hash": data_hash}
        del_req = _delete_document(column_target, query)
        logger.debug(f"Deletion Request Returned: {del_req}")


    # Prepare Blob into MongoDB Record
    inserted_ids = []
    for pn, pg in data["allPages"].items():
        logger.debug(f"Processing Page Number ({pn}) and Following Page Data:\n{pg}")
        single_page = {
            "src_hash": data_hash,  # SHA-256 Hash of Master Source Document
            "page_number": pn,  # Page Number in Sequential Order
            "page_name": pg["name"],  # Page in Master Source Document
            "boxes": pg["boxes"]  # List of Box Locations
            } # no longer need since using our own table table extraction
        logger.debug(f"Sending Prepared Object to MongoDB: {single_page}")

        # Insert into MongoDB
        mongo_page_id = column_target.insert_one(single_page)
        logger.debug(f"Created Record ({mongo_page_id.inserted_id}) in MongoDB")

        # List of Unique MongoDB ObjectIDs
        inserted_ids.append(str(mongo_page_id.inserted_id))
    # This returns MongoDB ObjectIDs, Not to Be Confused with the SHA-256 Hash
    if inserted_ids:
        return {"Session_IDs": inserted_ids}
    else:
        raise HTTPException(500, "No data to return")


@app.post("/load-session")
def load_session_db_route(src_hash: DBLoadAttrs):
    """
    Loads all UI data associated with a given document's SHA-256 hash. For example,
    if you have an example.pdf, generate a SHA-256 Hash of the document, and send
    its hash to this endpoint to load any pre-existing associated information.

    Will return multiple pages associated with the document in a list

    :param src_hash: SHA-256 hash
    :returns: List containing JSON Objects with MongoDB ObjectID, Boxes, Page Name, and Translation

    { 'Session':
        ['{"_id": {"$oid": str},
        "boxes": [{"h": int, "text": "str", "translation": "", "type": "str", "w": int, "x": int, "y": int}],
        "page_name": "str",
        "page_number": "int",
        "src_hash": "str"}'
        ]
    }
    """
    logging.info(f"API endpoint 'load-session' request received")
    data = json.loads(src_hash.json())  # JSON Blob of Data
    hashkey = data["src_hash"]  # Extracted String Value of the Hash

    # If the Hashkey does NOT exist (i.e., checking if this value is False)
    if not _check_db_if_hash_already_exists(hashkey):
        logger.debug("Passed hash does NOT exist in the database, no records to load.")
        return {"Session": f"No matching records exist."}

    column_target = _connect_to_mongo()

    logger.debug(f'Attempting to find all pages associated with ({hashkey})...')

    # Adds all pages to a list that are tagged with the hashkey (value of src_hash JSON key)
    all_matches = []
    for x in column_target.find({"src_hash": hashkey}):
        returned_page = dumps(x, sort_keys=True, ensure_ascii=False)
        all_matches.append(returned_page)

    return {"Session": all_matches}


@app.post("/delete-all-documents")
def delete_all_documents_db_route():
    """
    Requires no parameters, upon receiving a POST Request this endpoint will delete ALL
    sessions and records in the MongoDB volume.

    If successful, returns {'Deleted': True, 'Deleted Count': <int num records deleted>}
    If failed, returns {'Deleted': False, 'Error': <err description>}

    :returns: Boolean True/False
    """
    logging.info(f"API endpoint 'delete-all-documents' request received")
    column_target = _connect_to_mongo()
    logger.debug(f"Preparing to Delete Records from ({column_target}) Collection")

    query = {}  # Filter to Find and Delete All Documents
    return _delete_document(column_target, query)
    # try:
    #     del_op = column_target.delete_many({})
    #     logger.debug(f"Deleted {del_op.deleted_count} from {column_target}")
    #     return {"Deleted": True, "Deleted Count": {del_op.deleted_count}}
    # except Exception as e:
    #     return {"Deleted": False, "Error": e}


@app.post("/delete-one-session")
def delete_one_db_route(src_hash: DBLoadAttrs):
    """
    Deletes all pages associated with a single document using the master source hash for a document

    If successful, returns {'Deleted': True, 'Deleted Count': <int num records deleted>}
    If failed, returns {'Deleted': False, 'Error': <err description>}

    :param src_hash: SHA-256 hash
    :returns: Boolean True/False
    """
    logging.info(f"API endpoint 'delete-one-session' request received")
    column_target = _connect_to_mongo()
    data = json.loads(src_hash.json())  # JSON Blob of Data
    hashkey = data["src_hash"]  # Extracted String Value of the Hash

    logger.debug(f"Preparing to Delete Document Pages Associated with {hashkey} from ({column_target}) Collection")

    # If the Hashkey does NOT exist (i.e., checking if this value is False)
    if not _check_db_if_hash_already_exists(hashkey):
        logger.debug("Passed hash does NOT exist in the database, no records to load.")
        return {"Session": f"No matching records exist."}

    # Deletes Pages Based on Document Hash
    query = {"src_hash": hashkey}  # Filter to Find All Documents with Specific 'src_hash'
    return _delete_document(column_target, query)
    # try:
    #     del_op = column_target.delete_many(query)
    #     logger.debug(f"Deleted {del_op.deleted_count} from {column_target}")
    #     return {"Deleted": True, "Deleted Count": {del_op.deleted_count}}
    # except Exception:
    #     return {"Deleted": False}

def _delete_document(column_target, query):
    """
    Deletes one or more documents based on a passed MongoDB Query using a MongoDB Connection

    :param column_target: Connection to a MongoDB Database from _connect_to_mongo()
    :param query: MongoDB filter to identify records of interest (e.g., {key_name: value})
    """

    try:
        del_op = column_target.delete_many(query)
        logger.debug(f"Deleted {del_op.deleted_count} from {column_target}")
        return {"Deleted": True, "Deleted Count": {del_op.deleted_count}}
    except Exception:
        return {"Deleted": False}


def _check_output_and_return_b64(entry: dict) -> dict:
    """
    Verifies whether the output location in each record (in the Job Record results passed to the function)
    exists on-system, if it does, the job has completed processing and the file is Bas64'd and provided to
    the user as a result. Otherwise the job has not completed processing or has failed and a None is returned.

    :param blob: Job record queried from the SQLite database
    """

    output_value = entry.get('output_location')
    uuid_value = entry.get('internal_id')
    name_value = entry.get('name')
    success_value = entry.get('success')
    failure_value = entry.get('failure')
    completed_value = entry.get('completed')
    qualified_path = Path(output_value)

    if qualified_path.exists():
        logger.debug(f"Confirmed a file exists at '{qualified_path}'.")
        data = json.loads(open(qualified_path, 'r').read())
        content = {
            "name": output_value,
            "internal_id": uuid_value,
            "data": data
        }

    else:
        content = {
            "name": output_value,
            "internal_id": uuid_value,
            "success": str(success_value),
            "failure": str(failure_value),
            "completed": str(completed_value)
        }
        logger.warning(f"File does not exist at '{qualified_path}'. Current status: {content}")
    return content


def _get_job_data(entry: dict) -> dict:
    """
    Return status of job requested

    :param entry: Job record queried from the SQLite database
    """
    return {
        "name": entry.get('output_location'),
        "internal_id": entry.get('internal_id'),
        "success": str(entry.get('success')),
        "failure": str(entry.get('failure')),
        "completed": str(entry.get('completed'))
    }

""" # no longer need since using our own table table extraction
@app.post("/generate-excel")
def generate_excel(input_image_data: Inputb64):
    logger.debug(f"input_image_data type: {input_image_data}")
    logger.debug(f"input_image_data b64data: {input_image_data.b64data}")

    buffer = io.BytesIO()
    buffer.seek(0)
    string_input = input_image_data.b64data
    byte_data = base64.b64decode(string_input)
    doc_page = img2table_Image(src=byte_data)
    ocr = TesseractOCR(n_threads=1, lang= "chi_sim+chi_tra") # +eng

    buffer = io.BytesIO()
    doc_page.to_xlsx(dest=buffer, ocr=ocr, implicit_rows=False, implicit_columns=False, borderless_tables=False, min_confidence=TABLE_CONFIDENCE_THRESHOLD)
    
    buffer.seek(0)

    # test_batch_endpoint()
    return StreamingResponse(buffer, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={"Content-Disposition": "attachment; filename=generated_excel.xlsx"})
"""


@app.post("/bulk-pipeline")
async def bulk_pipeline_route(files: List[UploadFile] = File(...)):
    """
    Accepts multiple image files via form-data and performs OCR + translation on each.
    Returns a list of results per file.
    """
    results = []

    for file in files:
        try:
            # Read bytes and open image
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))

            # Wrap image as base64 for existing pipeline
            b64_bytes = base64.b64encode(contents).decode()
            pipeline_input = PipelineRequestData(
                name=file.filename,
                b64data=b64_bytes,
                src_lang="chinese",
                dst_lang="english",
                image_type=INBOUND_IMAGE_TYPE.TEXT,  # or infer from filename
                metadata={},
                overlay="False"
            )

            output_pages, _ = process_ocr(pipeline_input)
            translated = translate_page_data(
                textwrapper=output_pages[0],  # assuming single-page image
                lang_in="chinese",
                lang_out="english",
                translator=translator
            )

            results.append({
                "filename": file.filename,
                "ocr_text": [d['text'] for d in translated['data']],
                "translation": [d['translation'] for d in translated['data']]
            })
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            results.append({
                "filename": file.filename,
                "error": str(e)
            })

    return results


