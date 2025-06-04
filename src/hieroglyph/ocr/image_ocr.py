# OCR implementation using tesseract or pytesseract
from PIL import Image
from typing import List, Dict, Tuple, Set, Union, Optional
from pathlib import Path
from tempfile import NamedTemporaryFile
from concurrent.futures import ThreadPoolExecutor
from base64 import b64decode
from pandas import DataFrame
from statistics import mean
from tesserocr import PyTessBaseAPI, PSM
# import tesserocr
from hieroglyph.utils.image import ImageWrapper
from hieroglyph.utils.text import TextWrapper, BoxData
from hieroglyph.ocr import (ENGLISH_PRINTABLE, DIAGRAM_CONFIDENCE_THRESHOLD, TEXT_CONFIDENCE_THRESHOLD, TABLE_CONFIDENCE_THRESHOLD,
                           ENGLISH_PUNCTUATION_WHITESPACE, CHARACTER_BLACKLIST, PUNCTUATION_WHITESPACE)
from hieroglyph.general import MAX_WORKERS, INBOUND_IMAGE_TYPE, internal_language_mapping


from logging import getLogger
logger = getLogger(__name__)


def get_text_from_images(source_image_to_list_of_boxes: Dict[ImageWrapper, List[ImageWrapper]],
                         language: str, cthreshold: int) -> List[TextWrapper]:
    """Return TextWrappers for each box found on the page image given"""
    pages_data = []
    for source_image, box_images in source_image_to_list_of_boxes.items():
        pages_data.append(
            TextWrapper(name=source_image.name,
                        language=language,
                        data=_threaded_extract(box_images, language, cthreshold))
        )
    return sorted(pages_data, key=lambda k: (len(k.data), k.overall_confidence), reverse=True)


def _threaded_extract(box_images: List[ImageWrapper], language: str, cthreshold: int) -> List[BoxData]:
    """Extract text from a list of images, with language being our input lang for pytesseract"""
    extracted_content: List[BoxData] = []
    _extract_and_write_func = lambda img: _extract_and_write(img, language, cthreshold)
    skipped, not_skipped = 0, 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for result in executor.map(_extract_and_write_func, box_images):
            if result:
                if isinstance(result, list):
                    extracted_content.extend(result)
                else:
                    extracted_content.append(result)
                not_skipped += 1
            else:
                skipped += 1

    logger.debug("_threaded_extract: returning all box data from source image")
    return extracted_content


def _extract_and_write(box_image: ImageWrapper, language: str, cthreshold: int) -> Optional[BoxData]:
    """THREADED: Extract text and return based on language provided
    """
    ocr_data = _ocr(box_image, language)
    box = _create_box_data(box_image, ocr_data, language, cthreshold)
    return box if box else None


def _create_box_data(box_image: ImageWrapper, box_ocr_data: List[Dict[str, str | float]],
                     language: str, cthreshold: int) -> BoxData | None:
    relevant_boxes = []
    logger.debug(f"Box Data: {box_image.name} Starting with {len(box_ocr_data)} boxes at {box_image._box}")
    if isinstance(box_ocr_data, list):
        ignore_box = True
        for char in box_ocr_data:
            char['text'] = str(char['text']).strip()
            if filtered := _filter_text(char, box_image, language):
                relevant_boxes.append(filtered)
                ignore_box = False
        if ignore_box:
            logger.debug(f"All found boxes {box_image.name} | {box_image._box} , were either"
                         f" (all english/punctuation when OCR for chinese/russian) or (all punctuation ), ignoring")
            return None

    else:
        if filtered := _filter_text(box_ocr_data, box_image, language):
            relevant_boxes = [filtered]

    logger.debug(f"{box_image.name} Found {len(relevant_boxes)} relevant boxes")
    box_mean = mean(char['conf'] for char in relevant_boxes) if relevant_boxes else 0.0
    from re import split as re_split

    # Split on sentence terminators (language-aware)
    sentences = [s.strip() for s in re_split(r'(?<=[。！？.!?])\s*', "".join(char['text'] for char in relevant_boxes)) if s.strip()]


    # threshold = TEXT_CONFIDENCE_THRESHOLD if box_image.image_type == INBOUND_IMAGE_TYPE.TEXT_BASED else DIAGRAM_CONFIDENCE_THRESHOLD
    if cthreshold:
        threshold = cthreshold
    elif box_image.image_type == INBOUND_IMAGE_TYPE.TEXT_BASED or box_image.image_type == INBOUND_IMAGE_TYPE.TEXT_BASED_LINES:
        threshold = TEXT_CONFIDENCE_THRESHOLD 
    elif box_image.image_type == INBOUND_IMAGE_TYPE.DIAGRAM_BASED:
        threshold = DIAGRAM_CONFIDENCE_THRESHOLD        
    else:
        threshold = TABLE_CONFIDENCE_THRESHOLD        
#        threshold = TEXT_CONFIDENCE_THRESHOLD if box_image.image_type == INBOUND_IMAGE_TYPE.TEXT_BASED else DIAGRAM_CONFIDENCE_THRESHOLD

    logger.debug(f"Image OCR received a confidence threshold value of: {threshold}")

    if sentences and box_mean >= threshold:
        box_data_list = []
        for sent in sentences:
            box_data_list.append(BoxData(
                text=sent,
                confidence=box_mean,
                bounding_box=box_image._box  # Could improve this later to shrink per sentence
        ))
        return box_data_list

    else:
        logger.warning(f"Box for {box_image.name} with dimensions {box_image._box} with text [{box_string}]"
                       f" had mean of {box_mean} below {threshold}")
    return None


def _filter_text(box_data: dict, box_image: ImageWrapper, language: str) -> dict:
    should_ignore_box: bool = _should_ignore_box(box_data, language)
    if box_data['conf'] > 0.0 and box_data['text'] and not should_ignore_box:
        logger.debug(f"Found relevant box_data {box_image._box} | {box_data['conf']}% confidence: [{box_data['text']}],"
                     f" Ignore box? {should_ignore_box}")
        return box_data
    else:
        logger.debug(f"Bad box_data {box_image._box} | {box_data['conf']}% confidence: [{box_data['text']}],"
                     f" Ignore box? {should_ignore_box}")
        return {}


def _should_ignore_box(box: dict, language: str,
                       ignore_language: str = internal_language_mapping("english").to_ocr()) -> bool:
    """
    If the source language is english, JUST ignore punctuation. If the source language is NOT english,
    ignore english AND punctuation.
    """
    if language.lower() == ignore_language:
        return (set(box['text']) < PUNCTUATION_WHITESPACE)
    else:
        return (set(box['text']) < ENGLISH_PUNCTUATION_WHITESPACE)


def _ocr(image: ImageWrapper, lang: str) -> List[Dict[str, str | float]]:
    """List of image text with average confidence score across all lines
    return [
        {
            "text": "text",
            "conf": 0.0
        }
    ]
    """
    logger.debug(f"OCR {image.name} to {lang}")
    try:
        characters: List[Dict[str, str | float]] = _retrieve_text_data(image=image, lang=lang)
        if characters and sum(c['conf'] for c in characters) <= 0:
            return _retrieve_text_data(image=image, lang=lang, psm=PSM.SPARSE_TEXT)
        return characters
    except Exception as e:
        logger.warning(f"Tesseract error from image {image.name} to data: {e}")
        image.save(f'ERROR-{image.name}.jpeg')
        raise


def _retrieve_text_data(image: ImageWrapper, lang: str, psm=None) -> List[Dict[str, str | float]]:
    """
    return [
        {
            "text": "text",
            "conf": 0.0
        }
    ]
    """
    if psm is None:
        if image.image_type == INBOUND_IMAGE_TYPE.DIAGRAM_BASED:
            psm = PSM.SINGLE_LINE
        elif image.image_type == INBOUND_IMAGE_TYPE.TEXT_BASED:
            psm = PSM.SINGLE_BLOCK
        elif image.image_type == INBOUND_IMAGE_TYPE.TEXT_BASED_LINES:
            psm = PSM.SPARSE_TEXT
        else:
            psm = PSM.SINGLE_COLUMN # has given better results for tables
        #psm = PSM.SINGLE_LINE if image.image_type == INBOUND_IMAGE_TYPE.DIAGRAM_BASED else PSM.SINGLE_BLOCK # try PSM.SINGLE_COLUMN for tables
    else:
        logger.debug(f"Re-OCR {image.name} as {psm} as the previous attempt was invalid")
    with PyTessBaseAPI(psm=psm, lang=lang) as api:
        api.SetVariable('tessedit_char_blacklist', CHARACTER_BLACKLIST)
        api.SetImage(image.get_pillow())
        # langs = api.GetAvailableLanguages()
        return [{"text": api.GetUTF8Text(), "conf": api.MeanTextConf()}]
