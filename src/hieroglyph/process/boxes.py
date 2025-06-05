from PIL import Image
from typing import List, Tuple
from pathlib import Path
import numpy as np

import cv2
from statistics import mean

import json
import math
from deskew import determine_skew
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import logging

from hieroglyph.utils.image import ImageWrapper
from hieroglyph.general import  INBOUND_IMAGE_TYPE
from hieroglyph.ocr import DIAGRAM_CONFIDENCE_THRESHOLD, TEXT_CONFIDENCE_THRESHOLD, TABLE_CONFIDENCE_THRESHOLD
from hieroglyph.general import internal_language_mapping, INBOUND_IMAGE_TYPE  # Defined in __init__.py

# from hieroglyph.pipeline import (process_ocr, validate_input_ocr_data, validate_lang, 
#                                 validate_input_pipeline_data, validate_input_translate_data)
from hieroglyph.translation.translator import Translator


from img2table.document import Image as img2table_Image
# from img2table.document import PDF
from img2table.ocr import TesseractOCR
import io

logger = logging.getLogger(__name__)

global_buffer_to_export = io.BytesIO()

"""
Grabbing Defined Enums from pipeline.py -- Defines the type of
processing that should be performed on images based on content
"""


def convert_given_boxes(source_image: ImageWrapper, transformed_image: ImageWrapper,
                        image_type: INBOUND_IMAGE_TYPE, given_boxes: List[List[int]]) -> List[ImageWrapper]:
    """Extract [x,y,w,h] from given image for OCR"""
    source_image_array = source_image.get_array()

    all_boxes: List[ImageWrapper] = []
    num_skipped, num_not_skipped = 0, 0
    # Iterate given boxes
    for num, rectangle in enumerate(sorted(given_boxes), start=1):
        # Get bounding rectangle
        x, y, w, h = rectangle
        if h < 3 or w < 3:
            logger.warning(f"{source_image.name} rectangle {num} too small (x,y,w,h): {(x, y, w, h)}")
            num_skipped += 1
            continue
        img_arr = source_image_array[y:y+h, x:x+w]
        num_not_skipped += 1

        final_image = ImageWrapper(src_image=img_arr,
                                   name=f"{source_image.name}.box.{num}.png",
                                   box=[x, y, w, h],
                                   image_type=image_type,
                                   normalize_size=True)

        all_boxes.append(final_image)

    logger.debug(f"Finished with given boxes for {source_image.name}: {num_skipped} were skipped,"
                 f" and {num_not_skipped} were processed")
    logger.debug(f"Boxes: {all_boxes}")
    return all_boxes


def get_bounding_boxes(source_image: ImageWrapper,
                       transformed_image: ImageWrapper,
                       image_type: INBOUND_IMAGE_TYPE,
                       scale_pairing: Tuple[int, int] | None = None,
                       debug_mode: bool = False) -> List[ImageWrapper]:
    """Take preprocessed images and extract bounding box images"""
    source_image_array = source_image.get_array()
    if debug_mode:
        debug_path = Path("assets/DEBUG")
        debug_path.mkdir(parents=True, exist_ok=True)
        debug_source_image_array: np.ndarray = source_image_array.copy()

    # Convert to binary and invert polarity
    __, inverted_binary_image = cv2.threshold(transformed_image.to_array(), 0, 255,
                                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # If the passed image is diagram-based
    if image_type == INBOUND_IMAGE_TYPE.DIAGRAM_BASED:
        logger.debug(f"Initializing Bounding Box Creation for ENUM Type: {image_type}")
        """
        This is currently the optimal setting for bounding boxes for diagram-based images
        """

        rectangles = find_diagram_rectangles(source_image, inverted_binary_image, scale_pairing)

    elif image_type == INBOUND_IMAGE_TYPE.TABLE_BASED: 
        logger.debug(f"Initializing Bounding Box Creation for ENUM Type: {image_type}") # putting table based here for now
        """
        This is currently the optimal setting for bounding boxes for diagram-based images
        """
        rectangles = find_table_rectangles(source_image, inverted_binary_image, scale_pairing)

    elif image_type == INBOUND_IMAGE_TYPE.TEXT_BASED or image_type == INBOUND_IMAGE_TYPE.TEXT_BASED_LINES:
        logger.debug(f"Initializing Bounding Box Creation for ENUM Type: {image_type}")
        """
        This is currently the optimal setting for bounding boxes for paragraph-based text-images
        """

        # ######### ORIGINAL ON DEV BRANCH
        # kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        # dilated_thresh = cv2.dilate(inverted_binary_image, kernel, iterations=5)
        # contours, _ = cv2.findContours(dilated_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (4, 4))
        dilated_thresh = cv2.dilate(inverted_binary_image, kernel, iterations=12)
        contours, _ = cv2.findContours(dilated_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        rectangles = [cv2.boundingRect(c) for c in contours]

        # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (8, 8))
        # dilated_thresh = cv2.dilate(inverted_binary_image, kernel, iterations=4)
        # contours, _ = cv2.findContours(dilated_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    else:
        SystemExit(f"The enumerator passed into var 'image_type' is invalid. It appears to be {image_type}")

    all_boxes: List[ImageWrapper] = []
    num_skipped, num_not_skipped = 0, 0
    # Iterate contours, find bounding rectangles, Sort by: area, y, x
    # for num, rectangle in enumerate(sorted(rectangles, key=lambda r: (r[1]*r[2], r[1], r[0])), start=1):
    # Iterate contours, find bounding rectangles, Sort by: y, x
    for num, rectangle in enumerate(sorted(rectangles, key=lambda r: (r[1], r[0])), start=1):
        # Get bounding rectangle
        x, y, w, h = rectangle
        if h < 3 or w < 3:
            logger.warning(f"{source_image.name} rectangle {num} too small (x,y,w,h): {(x, y, w, h)}")
            num_skipped += 1
            continue
        img_arr = source_image_array[y:y+h, x:x+w]
        num_not_skipped += 1
        final_image = ImageWrapper(src_image=img_arr,
                                   name=f"{source_image.name}.box.{num}.png",
                                   box=[x, y, w, h],
                                   image_type=image_type,
                                   normalize_size=True)
        if debug_mode:
            # DEBUG
            # cv2.imwrite(str(debug_path / final_image.name), final_image.get_array())
            cv2.rectangle(debug_source_image_array, (x, y), (x+w, y+h), (0, 255, 0), thickness=1)
            cv2.putText(
                img=debug_source_image_array,
                text=f"[{num}]{x},{y},{w},{h}",
                org=(x, y),
                color=(0, 255, 0),
                thickness=1,
                fontScale=0.5,
                fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL,
                lineType=cv2.LINE_AA
            )
            # END DEBUG

        all_boxes.append(final_image)

    logger.debug(f"Finished with boxes for {source_image.name}: {num_skipped} were skipped,"
                 f" and {num_not_skipped} were processed")
    logger.debug(f"Boxes: {all_boxes}")

    # DEBUG
    if debug_mode:
        debug_filename = debug_path / f"{source_image.name}.all_boxes.png"
        logger.debug(f"Output all_boxes: {debug_filename}")
        cv2.imwrite(str(debug_filename), debug_source_image_array)
    # END DEBUG

    return all_boxes 


def calculate_average_closest_box_proximity(rectangles: List[Tuple]) -> float:
    """
    1. sort the boxes by top left and bottom left points, then top right and bottom right points
    2. calculate distance between each point and the next (if on the same line?) edge case,
       right side box in line 1 and left side box in line 2
    3. average the distances and return that value
    """
    sorted_rectangles = sorted(rectangles, key=lambda r: (r[1], r[0]))
    distance_pairs = [(sorted_rectangles[i], sorted_rectangles[i+1]) for i in range(0, len(sorted_rectangles)-1)]
    # logger.debug(f"Sorted rectangles: {sorted_rectangles}")
    # logger.debug(f"Distance pairs: {distance_pairs}")
    distances = [get_distance(rectangle1, rectangle2) for rectangle1, rectangle2 in distance_pairs]
    average_distance = mean(distances)
    # logger.debug(f"Average distance across all boxes is {average_distance}")
    return average_distance


def get_distance(rectangle1: tuple, rectangle2: tuple) -> float:
    """Determine the pixel distance between two rectangles, based on the midpoint"""
    from math import dist
    x1, y1, w1, h1 = rectangle1
    x2, y2, w2, h2 = rectangle2
    point1 = (x1 + (0.5*w1), y1 + (0.5*h1))
    point2 = (x2 + (0.5*w2), y2 + (0.5*h2))
    distance = dist(point1, point2)
    # logger.debug(f"Distance between {point1} and {point2} is {distance}")
    return distance


def close_enough(current_values: Tuple[int, float], previous_values: Tuple[int, float]) -> bool:
    """
    Check if previous boxes and average box proximities are close enough for us to say
    that we've found a good block neighborhood value
    """
    TOLERANCE = 1.5
    if abs(current_values[0] - previous_values[0]) <= TOLERANCE and abs(current_values[1] - previous_values[1]) <= TOLERANCE:
        return True
    else:
        return False


def find_diagram_rectangles(source_image: ImageWrapper,
                            inverted_binary_image: np.ndarray,
                            scale_pairing: Tuple[int, int] | None) -> list:
    if not scale_pairing:
        logging.debug("No scale pairing provided, try to find one")
        actual_rectangles = _range_find_optimal_rectangles(source_image, inverted_binary_image)
        if not actual_rectangles:
            logging.warning("Range find optimal rectangles did not find an optimal value for block neighborhood"
                            " and constant, default to a scaled 5,5")
            scale_pairing = (5, 5)
        else:
            return actual_rectangles
    block, C = get_threshold_values_by_scale(*scale_pairing)
    thresh = cv2.adaptiveThreshold(inverted_binary_image,
                                   255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV,
                                   block,
                                   C)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    actual_rectangles = [r for c in contours if (r := cv2.boundingRect(c))[2] > 5 and r[3] > 5]
    return actual_rectangles

def find_table_rectangles(source_image: ImageWrapper,
                            inverted_binary_image: np.ndarray,
                            scale_pairing: Tuple[int, int] | None) -> list:
    """
    if not scale_pairing:
        logging.debug("No scale pairing provided, try to find one")
        actual_rectangles = _range_find_optimal_rectangles(source_image, inverted_binary_image)
        if not actual_rectangles:
            logging.warning("Range find optimal rectangles did not find an optimal value for block neighborhood"
                            " and constant, default to a scaled 5,5")
            scale_pairing = (5, 5)
        else:
            return actual_rectangles
    """

    # internal = internal_language_mapping("english").to_ocr()
    # src_langlang = self.input_lang()
    # source_lang = internal_language_mapping(self).to_ocr()
    translator = Translator()
    source_lang= translator.source_language

    ocr = TesseractOCR(n_threads=1, lang= "chi_sim+chi_tra") #+eng
    
    image_array = source_image.get_array()
    success, encoded = cv2.imencode('.png', image_array)
    if success:
        image_bytes = encoded.tobytes()
    else:
        raise ValueError("Failed to encode image to bytes")
    
    doc = img2table_Image(src=image_bytes)

    extracted_tables = doc.extract_tables(ocr=ocr, implicit_rows=False, implicit_columns=False, borderless_tables=False, min_confidence=TABLE_CONFIDENCE_THRESHOLD)
    actual_rectangles = []
    for table in extracted_tables:
        for row in table.content.values():
            for cell in row:
                x1 = cell.bbox.x1
                y1 = cell.bbox.y1
                x2 = cell.bbox.x2
                y2 = cell.bbox.y2
                h = y2-y1
                w = x2-x1
                # value = cell.value
                # x, y, w, h = cv2.boundingRect(contour)
                actual_rectangles.append((x1, y1, w, h))

    return actual_rectangles


def get_threshold_values_by_scale(density_scale: int, box_scale: int) -> Tuple[int, int]:
    """
    Use a sliding scale of 0-10 for box density and size to get a better approximation of block neighborhood
    and C for adaptiveThreshold
    """
    MIN_BLOCK: int = 5
    MAX_BLOCK: int = 50
    MIN_C: int = 0
    MAX_C: int = MAX_BLOCK
    MIN_SCALE: int = 1
    MAX_SCALE: int = 20

    if not (MIN_SCALE <= density_scale <= MAX_SCALE):
        raise ValueError(f"Improper density scale: {density_scale}, must be between {MIN_SCALE}-{MAX_SCALE}")
    if not (MIN_SCALE <= box_scale <= MAX_SCALE):
        raise ValueError(f"Improper box scale: {box_scale}, must be between {MIN_SCALE}-{MAX_SCALE}")
    block = MIN_BLOCK + math.ceil((MAX_BLOCK / MAX_SCALE) * (density_scale - 1))
    c = MIN_C + math.floor((MAX_C / MAX_SCALE) * (box_scale - 1))
    block = block if block % 2 == 1 else block - 1
    if c > block:
        return block, block
    else:
        return block, c


def _range_find_optimal_rectangles(source_image: ImageWrapper,
                                   inverted_binary_image: np.ndarray) -> list:
    """
    Find optimal rectangles by approximating a good C and block_neighborhood for adaptiveThreshold
    """
    C: int = 10
    found_block: int = 0
    previous_avg_prox, previous_num_boxes, previous_contours = 0.0, 0, None
    previous_rectangles: list = []
    actual_rectangles: list = []
    breakout = False
    for block in range(5, 39, 2):
        for C in range(0, block, 2):
            # DEBUG
            # debug_diagram_array = source_image.get_array().copy()
            # END DEBUG

            thresh = cv2.adaptiveThreshold(inverted_binary_image,
                                           255,
                                           cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY_INV,
                                           block,
                                           C)

            # DEBUG
            # cv2.imwrite(str(Path("assets/output") / f"{source_image.name}.Thresh.block-{block}.C-{C}.jpeg"), thresh)
            # END DEBUG

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            rectangles = [r for c in contours if (r := cv2.boundingRect(c))[2] > 3 and r[3] > 3]
            num_boxes = len(rectangles)

            # DEBUG
            # for rectangle in rectangles:
            #     num_boxes += 1
            #     x, y, w, h = rectangle
            #     cv2.rectangle(debug_diagram_array, (x, y), (x+w, y+h), (0, 255, 0), thickness = 1)
            # END DEBUG

            if len(rectangles) <= 1:
                logger.warning(f"Found {len(rectangles)} rectangles: set prox, rectangles, and boxes accordingly")
                avg_prox = 0

            else:
                avg_prox = calculate_average_closest_box_proximity(rectangles)
                if close_enough((num_boxes, avg_prox), (previous_num_boxes, previous_avg_prox)):
                    logger.debug(f"Found a good approximation of block neighborhood with: block {block - 2},"
                                 f" boxes: {previous_num_boxes}, avg_prox: {previous_avg_prox}")
                    actual_rectangles = previous_rectangles
                    breakout = True
                    break
            previous_avg_prox = avg_prox
            previous_num_boxes = num_boxes
            previous_rectangles = rectangles
        if breakout:
            break
    else:
        logger.error(f"Reached limit of finding neighborhood bound without finding appropriate metric value")
        return []
        # raise ValueError(f"ERROR finding neighborhood bound for image {source_image.name}, exiting for debug")
    return actual_rectangles
