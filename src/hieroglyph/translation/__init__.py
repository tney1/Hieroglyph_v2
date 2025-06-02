import re
import logging
from typing import List, Dict, Tuple

from hieroglyph.ocr import ENGLISH_PRINTABLE
from hieroglyph.utils.text import TextWrapper, BoxData
from hieroglyph.translation.translator import Translator

logger = logging.getLogger(__name__)


def translate_page_data(translator: Translator, textwrapper: TextWrapper, lang_in: str, lang_out: str) -> Dict:
    """Take in the translator and a textwrapper to translate from lang_in to lang_out"""
    _translator = lambda data: translator.translate(lang_in=lang_in, lang_out=lang_out, text=data)
    _threaded_translate_wrapper = lambda box: _threaded_translate(box, _translator)
    for result in map(_threaded_translate_wrapper, textwrapper.data):
        logger.debug(f"Retrieved data for {result}")
    logger.info("translate_page_data: returning all box data from source image")
    return textwrapper.to_dict()


def _threaded_translate(box_data: BoxData, _translator) -> BoxData:
    text_set = set(box_data.text.strip())
    # NOTE: if the set is all english characters, don't bother translating it,
    #  under the presumption that that is already in english
    if ENGLISH_PRINTABLE.intersection(text_set) == text_set:
        box_data.translation = re.sub(r'[\.\?\\]+', '.', box_data.text.strip())
    else:
        resp = _translator(box_data.text.strip())
        box_data.translation = re.sub(r'[\.\?\\]+', '.', resp[0])
    return box_data
