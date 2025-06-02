#! /usr/bin/env python3.11
"""
Python script to get started with how to submit content to the API, 
"""
from base64 import b64encode, b64decode
from argparse import ArgumentParser, ArgumentError, Namespace
from pathlib import Path
from json import dumps, loads
import sys
from typing import List, Dict, Tuple
from datetime import timedelta
from requests import post, Response
import pdf2image
from rich.logging import RichHandler
from random import randint
from rich.console import Console
from concurrent.futures import ThreadPoolExecutor
import logging
import json
import numpy as np
import cv2
import time
from multiprocessing import cpu_count as mp_cpu_count
import glob
from requests.exceptions import ConnectionError, HTTPError

logging.basicConfig(handlers=[RichHandler(show_level=True, show_time=False, show_path=False)], level=logging.DEBUG, format="%(asctime)s [%(threadName)s] %(message)s")
logger = logging.getLogger(__file__)

SUPPORTED_IMAGE_TYPES = ['.png', '.jpeg', '.jpg']
SUPPORTED_FILE_TYPES = SUPPORTED_IMAGE_TYPES + ['.txt'] 

# NOTE: You can turn this up if you have this script submitting from a different host than the API
# MAX_WORKERS = cpu_count + 1 if (cpu_count := mp_cpu_count()) > 1 else cpu_count
MAX_WORKERS = 4


def generate_translate_filename() -> str:
    return str(time.strftime(r'%Y-%m-%d_%H-%M-%S'))

def get_input_files(input_fileglobs: List[str]) -> List[Path]:
    """
    Generates list of file paths using the file names provided. If a PDF is received,
    converts each page to a png, saves them to the same directory as the document, and adds them to the list.

    :param input_filenames: List containing names of files for processesing (e.g., ['assets/ru_diagrams/03.png'])
    :return: List of paths
    """

    all_files = []
    all_input_files = []
    for fileglob in input_fileglobs:
        all_input_files.extend(glob.glob(fileglob, recursive=True))
    logger.info(f"Found the following files: {all_input_files}")
    for input_file in set(all_input_files):
        input_path = Path(input_file)
    
        if input_path.suffix == ".pdf":
            images = pdf2image.convert_from_path(pdf_path=input_path, dpi=500)

            for num, image in enumerate(images, start=1):
                filename = input_path.with_suffix(f".{num}.png")
                logger.debug(f"Saving image to {filename}")
                image.save(filename)
                all_files.append(filename)
        elif input_path.suffix in SUPPORTED_FILE_TYPES:
            all_files.append(input_path)
        else:
            logger.warning(f"File {input_path} of type {input_path.suffix} is not in the list of supported image types: {SUPPORTED_FILE_TYPES + '.pdf'}")
    logger.info(f"Found images: {all_files}")

    return all_files


def dump_responses_to_disk(returned_responses: List[dict | List[dict]] | dict, output_directory: Path):
    """
    Write returned data to disk if present

    :param returned_responses: Json responses from the API
    :param output_directory: Directory to write files to from the api
    """
    logger.info(f"Dumping {len(returned_responses)} responses to {output_directory}")
    output_directory.mkdir(parents=True, exist_ok=True)
    match returned_responses:
        case dict():
            handle_response(returned_responses, output_directory)
        case list():
            for response_data in returned_responses:
                match response_data:
                    case dict():
                        logger.debug("Response_data is a dictionary")
                        handle_response(response_data, output_directory)
                    case list():
                        logger.debug("Response_data is a dictionary")
                        for page_response in response_data:
                            handle_response(page_response, output_directory)
                    case _:
                        logging.fatal(f"Response error: {response_data}")
                        sys.exit(1)

def handle_response(response_data: dict, output_directory: Path):
    """
    Write either json or image data to a file in the output directory

    :param response_data: Json response from the API
    :param output_directory: Directory to write files to from the api
    """
    logger.debug(f"Response keys: {list(response_data.keys())}")
    if 'b64_overlay' in response_data:
        filename = (output_directory / Path(response_data['name']).name).with_suffix('.overlay.png')
        logger.debug(f"Writing image data for {response_data['name']}")
        write_image_data(filename, response_data['b64_overlay'])
    elif 'result' in response_data:
        generated_name = generate_translate_filename()
        filename = (output_directory / Path(generated_name)).with_suffix('.json')
        logger.debug(f"Writing translate json data for {response_data}")
        write_data(filename, response_data)
    else:
        filename = (output_directory / Path(response_data['name']).name).with_suffix('.json')
        logger.debug(f"Writing json data for {response_data['name']}")
        write_data(filename, response_data['data'])

def write_data(filename: Path, data: list | dict):
    """
    Write json data to a file in the output directory

    :param filename: Specific file to write data to
    :param data: Json response from the API
    """
    with open(filename, "w+") as fp:
        json.dump(data, fp, indent=1, ensure_ascii=False)
    logger.info(f"Finished writing json: {filename}")
    


def write_image_data(filename: Path, image_data: str):
    """
    Write image data to a file in the output directory

    :param filename: Specific file to write data to
    :param image_data: Image bytes, base64 encoded
    """
    data_bytes = b64decode(image_data)
    data_array = np.frombuffer(data_bytes, dtype=np.uint8)
    image = cv2.imdecode(data_array, flags=0)
    if image is not None:
        cv2.imwrite(str(filename), image)
        logger.info(f"Finished writing image: {filename}")
    else:
        with open(filename.with_suffix(".error"), 'wb+') as f:
            f.write(data_bytes)
        logger.error(f"The image data was invalid: See {filename}.")


def make_request(args: Namespace, jsondata: dict, index: int = None) -> list:
    """
    Make post request to the api, based on the provided args.function

    :param jsondata: Request data, including the image/text content to be processed
    :param index: Optional index for logging if making multiple requests
    """
    try:
        start_time = time.time()
        match args.function:
            case "text" | "diagram" | "table":
                if args.no_translate:
                    logger.debug(f"Submitting '{jsondata['image_type']} OCR and Translate' job to {args.url}/ocr, Flag set to redirect request to /ocr due to usage of --no-translate")
                    response = post(f"{args.url}/ocr", json=jsondata)
                else:
                    logger.debug(f"Submitting '{jsondata['image_type']} OCR and Translate' job to {args.url}/pipeline")
                    response = post(f"{args.url}/pipeline", json=jsondata)

            case "batch":
                logger.debug(f"Submitting 'batch-pipeline' job to {args.url}/batch-pipeline")
                response = post(f"{args.url}/batch-pipeline", json=jsondata)
            case "translate":
                logger.debug(f"Submitting 'translate' job to {args.url}/translate")
                response = post(f"{args.url}/translate", json=jsondata)
            case "status":
                logger.debug(f"Submitting 'batch-status' job to {args.url}/batch-status")
                response = post(f"{args.url}/batch-status", json=jsondata)
            case _:
                raise Exception(f"Error: Invalid job args.function: {function}")
                return None
        logger.debug(f"Got response from API: {response}")
        response.raise_for_status()
        logger.debug(f"Finished request {index if index is not None else 1} after: {timedelta(seconds=time.time() - start_time)}")
        
        try:
            return response.json()
        except json.JSONDecodeError as e:
            logger.warning(f"Error, no json to find: {e} -> {response.text}")
            raise

    except ConnectionError as e:
        if "Max retries exceeded with args.url" in str(e):
            logger.error(f"ERROR: Make sure the API is running")
        else:
            logger.error(f"Connection ERROR: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(e)
        raise


def prep_request_data(args: Namespace, input_filepath: Path) -> dict:
    """Prepare the request data json for submission"""
    if args.function == "diagram" or args.function == "text" or args.function == "table" or args.function == "batch":
        input_base64 = b64encode(open(input_filepath, 'rb').read())

        jsondata = {
            "name": Path(input_filepath).name,
            "src_lang": args.src_lang,
            "dst_lang": args.dst_lang,
            "b64data": input_base64.decode('utf-8'),
            "image_type": args.function if args.function != "batch" else "text",
            "overlay": str(args.overlay)
        }
        if args.function == "diagram" and not (args.box_scale is None or args.density_scale is None):
            jsondata.update({
                "box_scale": args.box_scale,
                "density_scale": args.density_scale
            })
        
        if args.conf is not None:
            jsondata.update({
                "conf_threshold": args.conf
            })

        debug_data = {key: value for key, value in jsondata.items() if key != 'b64data'}
    elif args.function == "translate":

        logger.debug(f"Preparing submission for {args.url}/translate")
        content = open(input_filepath, 'r').read()
        jsondata = {
            "text": content,
            "src_lang": args.src_lang,
            "dst_lang": args.dst_lang,
        }
        debug_data = {key: value for key, value in jsondata.items() if key != 'text'}

    else:
        logger.fatal("Did not receive a valid endpoint from the '-f' or '--function' argument. Please try again.")
        sys.exit(1)
    logger.debug(f"Prepped data: {dumps(debug_data, indent=1, ensure_ascii=False)}")
    return jsondata


def submit_pipeline_content(input_files: List[Path], args: Namespace) -> List[Response] | None:
    """
    Responsible for transmission of pipeline files to URL

    :param input_files: List of paths to files for processesing or list of strings to translate (e.g., ['assets/ru_diagrams/03.png'])
    :param function: API endpoint to send JSON request ('text' or 'diagram' or 'table')

    :return: JSON response with the outcome from the API
    """
    def _execute_pipeline(args: Namespace, input_filepath: Path, index: int) -> list:
        jsondata = prep_request_data(args, input_filepath)
        return make_request(args, jsondata, index)

    first_start_time = time.time()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    _pipeline_wrapper = lambda index_path: _execute_pipeline(args=args, input_filepath=index_path[1], index=index_path[0])
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for result in executor.map(_pipeline_wrapper, enumerate(input_files, start=1)):
            logger.debug(f"Retrieved data at {timedelta(seconds=time.time() - first_start_time)}")
            dump_responses_to_disk(result, args.output_directory)


    logger.debug(f"FINISHED {len(input_files)} requests IN: {timedelta(seconds=time.time() - first_start_time)}")


def submit_text_content(args: Namespace) -> list | None:
    """
    Responsible for transmission of text content to url  
    
    Subparameters of args:  

    :param content: Text content to submit to '人员和与值排班管理'
    :param function: API endpoint to send JSON request (e.g., 'translate')
    :param url: HTTP URL of the endpoint to submit jobs to (e.g., http://127.0.0.1:8088)
    :param src_lang: Source language for input file
    :param dst_lang: Destination language for response
    :param overlay: True/False indicator of whether to return the base64 of the image with overlayed text
    :return: JSON response with the outcome from the API
    """
    if args.function == "translate":
        logger.debug(f"Preparing submission {args.content} for {args.url}/translate")
        jsondata = {
            "text": args.content,
            "src_lang": args.src_lang,
            "dst_lang": args.dst_lang,
        }
        logger.debug(f"Data to send:\n{dumps(jsondata, indent=2, ensure_ascii=False)}\n")
        return make_request(args, jsondata)

    else:
        logger.error("Did not receive a valid endpoint from the '-f' or '--function' argument when paired with the '-c'/'--content' or '-i'/'--input' arguments. Please try again.")
        raise Exception("Invalid content type with function translate")


def retrieve_and_write_batch_content(batch_responses: List[dict], args: Namespace) -> list | None:
    """
    
    :param batch_responses: all name and internal ids for the generated data

    Subparameters of args:  
    :param content: Text content to submit to '人员和与值排班管理'
    :param function: API endpoint to send JSON request (e.g., 'translate')
    :param url: HTTP URL of the endpoint to submit jobs to (e.g., http://127.0.0.1:8088)
    :param src_lang: Source language for input file
    :param dst_lang: Destination language for response
    :param overlay: True/False indicator of whether to return the base64 of the image with overlayed text
    """
    args.function = "status"
    while batch_responses:
        logger.debug(f"Re-checking on batch_responses, currently: {batch_responses}")

        for name_id in batch_responses:
            logger.debug(f"Checking on: {name_id}")
            response = make_request(args, {
                "internal_id": name_id['internal_id']
            })
            if 'data' in response:
                logger.debug(f"{name_id} is FINISHED according to response: {response['name']} | {response['internal_id']} | data...")
                dump_responses_to_disk(response['data'], args.output_directory)
            else:
                logger.debug(f"{name_id} is not yet finished according to {response}")
            name_id.update(**response)
        batch_responses = [response for response in batch_responses if 'data' not in response]
        if batch_responses:  
            sleep_time = 30
            logger.info(f"Unfinished jobs left, sleeping for {sleep_time} seconds to give the API a chance to finish processing...")
            time.sleep(sleep_time)


def submit_batch_content(input_files: List[Path], args: Namespace) -> list | None:
    """
    Responsible for transmission of batch pipeline files to URL

    :param input_files: List of paths to files for processesing or list of strings to translate (e.g., ['assets/ru_diagrams/03.png'])
    
    Subparameters of args:  
    :param content: Text content to submit to '人员和与值排班管理'
    :param function: API endpoint to send JSON request (e.g., 'translate')
    :param url: HTTP URL of the endpoint to submit jobs to (e.g., http://127.0.0.1:8088)
    :param src_lang: Source language for input file
    :param dst_lang: Destination language for response
    :param overlay: True/False indicator of whether to return the base64 of the image with overlayed text

    :return: JSON response with the outcome from the API
    """
    first_start_time = time.time()
    args.output_directory.mkdir(parents=True, exist_ok=True)

    jsondata = {
        "images": [prep_request_data(args, input_filepath) for input_filepath in input_files]
    }

    generated_ids: list = make_request(args, jsondata)
    logger.debug(f"Sent batch pipeline data for {len(input_files)} files, time elapsed: {timedelta(seconds=time.time() - first_start_time)}")
    logger.debug(f"{generated_ids=}")
    return generated_ids



def main(args: Namespace):
    """
    Collects list of file paths and transmits them to the API. This is the function that should be called if imported
    into other applications to communicate with the API without using subprocess commands and manual flags.

    :param args: Namespace containing all the passed args: Can be manually created with Namespace(input=[Path('input/**.pdf')], url='http://localhost:8088', src_lang='chinese', dst_lang='english', function='diagram', overlay=True, output_directory=Path().cwd()) from the argparse library
    :return: JSON response with the outcome from the API
    """
    responses = []
    if args.input:
        input_files = get_input_files(args.input)
        if args.function == "batch":
            batch_responses = submit_batch_content(input_files, args)
            retrieve_and_write_batch_content(batch_responses, args)
        else:
            responses = submit_pipeline_content(input_files, args)
    elif args.content:
        responses = [submit_text_content(args)]
        dump_responses_to_disk(responses, args.output_directory)
    else:
        raise Exception(f"Must provide either input files (--input), or text to translate (--content)")


if __name__ == "__main__":
    exec_start = time.time() 
    parser = ArgumentParser(__file__)

    parser.add_argument("-i", "--input", required=False, nargs="+",
                        help="Fileglobs to retrieve files from: (recursively gathers files matching the globs,b64 encodes them and submitts them to the API: e.g. --input='./input/*.pdf' --input='./documents/*.png' --input='/home/Desktop/**.pdf')")
    parser.add_argument("-c", "--content", required=False,
                        help="String content to translate ('人员和与值排班管理')")
    parser.add_argument("-u", "--url", required=False, default="http://localhost:80", 
                        help="HTTP URL of the endpoint to submit jobs to (e.g., http://127.0.0.1:8088)") 
    parser.add_argument("-s", "--src-lang", type=lambda s: str(s).lower(), required=False, default="chinese",
                        help="Source language for input file ex. 'chinese' (Chinese Simplified or Traditional)")
    parser.add_argument("-d", "--dst-lang", type=lambda s: str(s).lower(), required=False, default="english",
                        help="Destination language for input file ex. 'eng' (English)")
    parser.add_argument("-bs", "--box-scale", type=int, choices=range(1,11), required=False, help="Scale for the boxes from 1-10 with 1 being bigger boxes and 10 being smaller boxes")
    parser.add_argument("-ds", "--density-scale", type=int, choices=range(1,11), required=False, help="Scale for the boxes from 1-10 with 1 being less dense boxes and 10 being more dense boxes")
    parser.add_argument("-f", "--function", required=False, default="diagram",
                        type=lambda s: str(s).lower().strip(), choices=["text", "diagram", "table", "translate", "batch"],
                        help="Which api function to use: 'text', 'diagram', 'table', 'translate', 'batch'")
    parser.add_argument('-o', "--overlay", required=False, action='store_true',
                        help="Trigger return of base64'd overlayed text translation in the JSON return")
    parser.add_argument('-od', "--output-directory", required=False, type=Path, default=Path().cwd() / "submitter-data",
                        help="Directory to output for overlays")
    parser.add_argument('-nt', '--no-translate', required=False, action='store_true',
                        help="Marks requests to ONLY receive OCR bounding boxes with no translations processed")
    parser.add_argument("-cf", "--conf", type=int, choices=range(0,100), required=False, help="Scale which sets the confidence threshold dynamically to adjust the tolerance level of OCR")



    args = parser.parse_args()
    logger.debug(f"Args: {args}")
    main(args)
    logger.info(f"Complete execution time: {timedelta(seconds=time.time() - exec_start)}")
