# Threaded class to be called from the api that processes the file(s),
#  does image improvement, ocr, then translation before returning results
from typing import List, Dict, Tuple, Union, Optional
from base64 import b64decode
from PIL import Image
from fastapi.exceptions import HTTPException
import logging

from hieroglyph.process import process_data
from hieroglyph.ocr.image_ocr import get_text_from_images
from hieroglyph.models import (BatchPipelineRequestData, OCRRequestData, TranslateRequestData,
                              ImageRequestData, PipelineRequestData)
from hieroglyph.ocr import DIAGRAM_CONFIDENCE_THRESHOLD, TEXT_CONFIDENCE_THRESHOLD, TABLE_CONFIDENCE_THRESHOLD
from hieroglyph.utils.image import ImageWrapper
from hieroglyph.utils.text import TextWrapper
from hieroglyph.general import internal_language_mapping, INBOUND_IMAGE_TYPE  # Defined in __init__.py

logger = logging.getLogger(__name__)


def process_ocr(input_image_data: ImageRequestData,
                debug: bool = False) -> Tuple[List[TextWrapper], Optional[Dict[ImageWrapper, List[ImageWrapper]]]]:
    """
    Return list of textwrappers corresponding to the data found when OCRing the input image. debug=True will return preprocessed images as well
        return
        (
            [
                TextWrapper{
                    "name": "name of the image we are working on",
                    "language": "tesseract langauge we used to ocr content",
                    "overall_confidence": 0.0, # float value = average of box data confidence values
                    "data": [
                        BoxData
                    ]
                }
            ],
            None
        )
        OR
        (
            [
                TextWrapper{
                    "name": "name of the image we are working on",
                    "language": "tesseract langauge we used to ocr content",
                    "overall_confidence": 0.0, # float value = average of box data confidence values
                    "data": [
                        BoxData
                    ]
                }
            ],
            {
                ImageWrapper: # Transformed Page ImageWrapper
                [
                    ImageWrapper: {} # Individual boxes on Transformed Page ImageWrapper
                ]
            }
        )
    """
    preprocessed_data: Dict[ImageWrapper, List[ImageWrapper]] = process_data(
        input_image_data=input_image_data,
        debug_mode=debug,
        boxes=input_image_data.boxes if hasattr(input_image_data, "boxes") else []
    )

    # Saving Confidence Threshold
    if input_image_data.conf_threshold != None:
        confidence_threshold = input_image_data.conf_threshold
        logger.debug(f"Confidence threshold set by user to: {confidence_threshold}")
    elif input_image_data.image_type == INBOUND_IMAGE_TYPE.TEXT_BASED:
        confidence_threshold = TEXT_CONFIDENCE_THRESHOLD 
    elif input_image_data.image_type == INBOUND_IMAGE_TYPE.DIAGRAM_BASED:
        confidence_threshold = DIAGRAM_CONFIDENCE_THRESHOLD        
    else:
        confidence_threshold = TABLE_CONFIDENCE_THRESHOLD    
    
    # else:
    #     confidence_threshold = TEXT_CONFIDENCE_THRESHOLD if input_image_data.image_type == INBOUND_IMAGE_TYPE.TEXT_BASED else DIAGRAM_CONFIDENCE_THRESHOLD
    #     logger.debug(f"Using default confidence threshold: {confidence_threshold}")

    logger.debug("Finished OCR, moving to translation")
    
    from hieroglyph.translation.smart_translate import translate_by_line_or_sentence

    for textwrapper in image_name_to_language_extractions:
        for box in textwrapper.data:
            original_text = box["text"]
            translated_lines = translate_by_line_or_sentence(
                original_text,
                source_lang=input_image_data.src_lang,
                target_lang=input_image_data.dst_lang
            )
            box["translated"] = translated_lines  # Add translated content to each box

    logger.debug("Finished translating OCR output")

    return (image_name_to_language_extractions, preprocessed_data) if debug else (image_name_to_language_extractions, None)


def validate_input_ocr_data(input_image_data: OCRRequestData) -> OCRRequestData:
    """Validate input image data for ocr requests, make conversions as necessary"""
    logger.debug(f"Received src language of {input_image_data.src_lang}")

    _validate_image_data(input_image_data)
    input_image_data.src_lang = _validate_lang(input_image_data.src_lang, 'src_lang')
    input_image_data.image_type = _validate_image_type(input_image_data.image_type)
    logger.debug(f"OCR conf: {input_image_data.conf_threshold}")
    input_image_data.conf_threshold = input_image_data.conf_threshold if input_image_data.conf_threshold and input_image_data.conf_threshold < 100 and input_image_data.conf_threshold >= 0 else None
    logger.debug(f"OCR source, image, conf: {input_image_data.src_lang}, {input_image_data.image_type}, {input_image_data.conf_threshold}")
    return input_image_data


def validate_input_pipeline_data(input_image_data: PipelineRequestData) -> PipelineRequestData:
    """Validate input image data for pipeline requests (batch and single), make conversions as necessary"""
    logger.debug(f"Received src language of {input_image_data.src_lang}")
    logger.debug(f"Received dst language of {input_image_data.dst_lang}")
    logger.debug(f"Received overlay status of {input_image_data.overlay}")

    _validate_image_data(input_image_data)
    input_image_data.src_lang = _validate_lang(input_image_data.src_lang, 'src_lang')
    input_image_data.dst_lang = _validate_lang(input_image_data.dst_lang, 'dst_lang')
    input_image_data.image_type = _validate_image_type(input_image_data.image_type)
    return input_image_data


def validate_input_translate_data(input_translate_data: TranslateRequestData) -> TranslateRequestData:
    """If there is no text field specified as well as src/dst langs, return an HTTP 400 Error - Else, run as normal."""
    logger.debug(f"Received: {input_translate_data}")
    logger.debug(f"Received src language of {input_translate_data.src_lang}")
    logger.debug(f"Received dst language of {input_translate_data.dst_lang}")
    if input_translate_data.text == "" or not input_translate_data.text:
        raise HTTPException(400, "Text field is empty, check the contents of your request.")
    input_translate_data.src_lang = _validate_lang(input_translate_data.src_lang, 'src_lang')
    input_translate_data.dst_lang = _validate_lang(input_translate_data.dst_lang, 'dst_lang')
    return input_translate_data


def _validate_image_data(input_image_data: ImageRequestData):
    """Validate the name, b64data, and boxes, return an HTTP 400 Error - Else, run as normal."""
    if input_image_data.name == "" or not input_image_data.name:
        raise HTTPException(422, "'name' field is empty, check the contents of your request.")

    if input_image_data.b64data == "" or not input_image_data.b64data:
        raise HTTPException(422, "'b64data' field is empty, check the contents of your request.")

    if input_image_data.boxes:
        # NOTE: This is just an arbitrary limit
        if len(input_image_data.boxes) > 500:
            raise HTTPException(422, f"Invalid number of boxes provided: {len(input_image_data.boxes)}, max is 500")
        if any(len(box) != 4 for box in input_image_data.boxes):
            raise HTTPException(422, f"Invalid boxes provided: {input_image_data.boxes}, must be of the format [[x1,y1,w1,h1], [x2,y2,w2,h2]]")


def _validate_image_type(image_type: str) -> INBOUND_IMAGE_TYPE:
    """Validate the image type field, return an HTTP 400 Error - Else, run as normal."""
    try:
        return INBOUND_IMAGE_TYPE(image_type)
    except ValueError as e:
        raise HTTPException(400, f"Improper image type, '{image_type}', please specify either 'diagram' or 'text'")


def _validate_lang(image_lang: str, lang_src: str) -> str:
    """Validate the language is proper, return the converted version if it's good"""
    try:
        logging.debug(f"Attempting to convert '{lang_src}' using internal mappings.")
        converted_lang = internal_language_mapping(image_lang).to_ocr()
        logging.debug(f"Converted '{lang_src}' of {image_lang} to {converted_lang}")

    except Exception as e:
        raise HTTPException(400, f"Your '{lang_src}' is broken. Fix request and try again.")

    if converted_lang is None:
        raise HTTPException(400, f"The '{lang_src}' does not conform. Check spelling.")


    return converted_lang
