# from hieroglyph.utils.image import ImageWrapper

from typing import Union, Dict, List, Optional, Tuple
from statistics import mean
import numpy as np
import cv2
import textwrap
from base64 import b64encode
from pathlib import Path
import math
import logging

logger = logging.getLogger(__name__)


def classify_text_type(ocr_text: str) -> str:
    """
    Classifies OCR text as either 'code' or 'prose' using basic heuristics.
    """
    code_indicators = ['{', '}', ';', 'def ', 'class ', '#', '//', 'import ', 'return ', '->']
    lines = ocr_text.splitlines()
    code_lines = [line for line in lines if any(indicator in line for indicator in code_indicators)]

    return "code" if len(code_lines) / max(len(lines), 1) >= 0.3 else "prose"


class BoxData:
    """
    {
        "text": "script character found in the box",
        "confidence": 0.0, # average confidence across characters in the box
        "bounding_box": [x,y,w,h],
        "translation": "dst_lang translated content,
    }
    """
    __slots__ = ("text", "confidence", "bounding_box", "translation")

    def __init__(self, text: str, confidence: float, bounding_box: list, translation: str = ""):
        self.text = str(text).strip()
        self.confidence = confidence
        self.bounding_box = bounding_box
        self.translation = translation

    def update_translation(self, translation: str):
        self.translation = str(translation).strip()

    def __eq__(self, o) -> bool:
        return True if self.text == o.text and self.confidence == o.confidence and \
            self.bounding_box == o.bounding_box and self.translation == o.translation else False

    def to_dict(self) -> Dict[str, Union[str, float, List[float]]]:
        return {"text": self.text,
                "confidence": self.confidence,
                "bounding_box": self.bounding_box,
                "translation": self.translation}

    def __str__(self) -> str:
        return f"<BoxData: {self.text=}, {self.confidence=}, {self.bounding_box=}, {self.translation=}>"

    __repr__ = __str__


class TextWrapper:
    """
    {
        "name": "name of the image we are working on",
        "language": "tesseract langauge we used to ocr content",
        "overall_confidence": 0.0, # float value = average of box data confidence values
        "data": [
            BoxData
        ]
    }
    """
    __slots__ = ("name", "data", "language", "overall_confidence")

    def __init__(self, name: str, language: str, data: List[BoxData]):
        self.name = name
        self.language = language
        self.data = sorted(data, key=lambda b: (b.bounding_box[1], b.bounding_box[0]))
        self.overall_confidence = mean(x.confidence for x in self.data if x.confidence > 0.0) if self.data else 0.0

    def to_dict(self) -> Dict[str, list | float | str]:
        return {
            "name": self.name,
            "language": self.language,
            "overall_confidence": self.overall_confidence,
            "data": [box.to_dict() for box in self.data]
        }

    def __eq__(self, o) -> bool:
        return True if self.name == o.name and self.overall_confidence == o.overall_confidence and \
            self.language == o.language and self.data == o.data else False

    def overlay(self, image_array: np.ndarray, debug: bool = False) -> str:
        """Overlay translated text boxes onto given image, return the image as a b64 encoded string"""
        line_gap = 2
        font_face = cv2.FONT_HERSHEY_COMPLEX_SMALL
        scaling_factor_start = 2.0
        for box_data in self.data:
            logger.debug(f"Making box in {self.name} for overlay {box_data}")
            x, y, w, h = box_data.bounding_box

            number_of_target_characters_to_fill_box, font_height = get_num_chars_from_pixel_width_and_height(text=box_data.translation,
                                                                                                             font_scale=scaling_factor_start,
                                                                                                             box_width=w+2,
                                                                                                             font_face=font_face)
            lines = textwrap.wrap(text=box_data.translation, width=number_of_target_characters_to_fill_box, tabsize=2,
                                  drop_whitespace=True, break_long_words=False)
            lines, font_scale, font_height = get_font_scale(text=box_data.translation, font_scale=scaling_factor_start,
                                                            font_height_pxl=font_height, lines=lines, box_width_pxl=w+1,
                                                            box_height_pxl=h+1)
            if font_scale <= 0.2:
                logger.debug(f"Font scale ({font_scale}) is too small, ignore this box for {x}, {y}, {w}, {h}")
                continue
            else:
                logger.debug(f"Font scale is {font_scale} for {x}, {y}, {w}, {h}")

            image_array = cv2.rectangle(image_array, (x + 1, y + 1), (x + w + 1, y + h + 1), (255, 255, 255), thickness=-1)
            image_array = cv2.rectangle(image_array, (x - 1, y - 1), (x + w + 3, y + h + 2), (0, 0, 0), thickness=1)

            for index, text in enumerate(lines, start=1):
                # logger.debug(f"Line to put for box: {text} -> {y + (index * (font_height + line_gap))}")
                image_array = cv2.putText(
                    img=image_array,
                    text=text,
                    org=(x, y - line_gap + (index * (font_height + line_gap))),
                    color=(0, 255, 0),
                    thickness=1,
                    fontScale=font_scale,
                    fontFace=font_face,
                    lineType=cv2.LINE_AA
                )
        # if debug:
        #     debug_path = Path("assets/output")
        #     debug_path.mkdir(parents=True, exist_ok=True)
        #     output_file = debug_path / f"{self.name}.overlayed.png"
        #     logger.debug(f"If the overlay flag was marked as TRUE, an overlay will be written to {output_file}."
        #                  f" Disregard otherwise.")
        #     cv2.imwrite(str(output_file), image_array)
        return encode_image_array(image_array)


def get_num_chars_from_pixel_width_and_height(text: str, font_scale: float,
                                              box_width: int, font_face: int) -> Tuple[int, int]:
    """
    Determine the number of characters you can fit into a box of box_width pixels
    based on the font scale and corresponding font width
    """
    (full_text_width, full_text_height), baseline = cv2.getTextSize(text=text, fontFace=font_face,
                                                                    fontScale=font_scale, thickness=1)
    # logger.debug(f"GetTextSize debug: [{text}], {font_scale=}, {box_width=}, {font_face=}")
    target_character_pixel_width = full_text_width / len(text)
    number_of_target_characters_to_fill_box = box_width / target_character_pixel_width
    chars = math.floor(number_of_target_characters_to_fill_box)
    # logger.debug(f"It takes {chars} characters to fill {box_width}")
    return chars if chars > 0 else 1, full_text_height


def get_font_scale(text: str, font_scale: float, font_height_pxl: int, lines: List[str],
                   box_width_pxl: int, box_height_pxl: int, font_face: int = cv2.FONT_HERSHEY_COMPLEX_SMALL,
                   line_gap_pxl: int = 1) -> Tuple[list, float, int]:
    """Recursively determine the font scale for text given a specific bounding box it should fit in"""
    TOO_SMALL = 0.2
    FONT_SCALE_DECREMENT = 0.1
    line_width_good = all(cv2.getTextSize(text=line,
                                          fontFace=font_face,
                                          fontScale=font_scale,
                                          thickness=1)[0][0] <= box_width_pxl for line in lines)
    line_height_good = ((font_height_pxl + line_gap_pxl) * len(lines)) < box_height_pxl
    if (line_height_good and line_width_good) or (font_scale <= TOO_SMALL):
        # logger.debug(f"BASE CASE [{text}]: font height pixel: {font_height_pxl}, lines: {len(lines)},"
        #              f" box height: {box_height_pxl}, lines * height < box height?"
        #              f" {(((font_height_pxl + line_gap_pxl) * len(lines)) < box_height_pxl)}"
        #              f" font scale: {font_scale}, too small?: {(font_scale <= TOO_SMALL)}")
        return lines, font_scale, font_height_pxl
    new_font_scale = font_scale - FONT_SCALE_DECREMENT
    number_of_target_characters_to_fill_box, font_height = get_num_chars_from_pixel_width_and_height(text=text,
                                                                                                     font_scale=new_font_scale,
                                                                                                     box_width=box_width_pxl,
                                                                                                     font_face=font_face)
    new_lines = textwrap.wrap(text=text, width=number_of_target_characters_to_fill_box,
                              tabsize=2, drop_whitespace=True, break_long_words=False)
    return get_font_scale(text=text, font_scale=new_font_scale, font_height_pxl=font_height,
                          lines=new_lines, box_width_pxl=box_width_pxl, box_height_pxl=box_height_pxl,
                          font_face=font_face, line_gap_pxl=line_gap_pxl)


def encode_image_array(image_array: np.ndarray) -> str:
    """Encode a numpy array image as a base64 string"""
    _, encoded_image = cv2.imencode('.png', image_array)
    return b64encode(encoded_image).decode('utf-8')
