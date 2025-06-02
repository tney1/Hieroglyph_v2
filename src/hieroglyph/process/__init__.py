
from hieroglyph.process.image_processing import preprocess_data
from hieroglyph.models import ImageRequestData
from hieroglyph.process.boxes import get_bounding_boxes, convert_given_boxes
from hieroglyph.utils.image import ImageWrapper
from typing import List, Dict
from PIL import Image
from hieroglyph.general import INBOUND_IMAGE_TYPE
import logging

logger = logging.getLogger(__name__)


def process_data(input_image_data: ImageRequestData, debug_mode: bool,
                 boxes: List[List[int]] = []) -> Dict[ImageWrapper, List[ImageWrapper]]:
    """
    Convert input image data to list of preprocessed ImageWrappers
    """
    converted_data: ImageWrapper = ImageWrapper(src_image=input_image_data.b64data,
                                                name=f"{input_image_data.name}",
                                                image_type=input_image_data.image_type,
                                                normalize_size=False)
    logger.debug(f"Finished image conversion, moving on to preprocessing with {converted_data}")
    processed_image: ImageWrapper = preprocess_data(converted_data)
    logger.debug("Finished preprocessing, ask opencv for bounding boxes in the images")
    scale_pairing = (input_image_data.density_scale, input_image_data.box_scale) if input_image_data.density_scale and input_image_data.box_scale else None
    source_image_to_boxes: Dict[ImageWrapper, List[ImageWrapper]] = {
        converted_data: convert_given_boxes(source_image=converted_data,
                                            transformed_image=processed_image,
                                            image_type=input_image_data.image_type,
                                            given_boxes=boxes) if boxes else get_bounding_boxes(source_image=converted_data,
                                                                                                transformed_image=processed_image,
                                                                                                image_type=input_image_data.image_type,
                                                                                                scale_pairing=scale_pairing,
                                                                                                debug_mode=debug_mode)
    }
    return source_image_to_boxes
