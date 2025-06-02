# add preprocessing of images here
from typing import List
from hieroglyph.utils.image import ImageWrapper
from hieroglyph.process.threshold import threshold_image, gaussian_threshold, \
                                        mean_threshold, global_threshold, median_blur
from hieroglyph.process.enhance import execute_enhancement_on_pil_img, test_pil_img
from PIL import Image
from pathlib import Path
import logging
logger = logging.getLogger(__name__)


def preprocess_data(image: ImageWrapper) -> ImageWrapper:
    """Take data, global threshold and enhance"""
    logger.debug(f"Thresholding {image.name}")



    modified_image_array = global_threshold(median_blur(image.to_array()))
    
    logger.debug(f"About to enhance {image.name}")
    enhanced_image = execute_enhancement_on_pil_img(Image.fromarray(modified_image_array))
    final_image = ImageWrapper(src_image=enhanced_image,
                               name=f"{image.name}.modified.png",
                               image_type=image.image_type,
                               normalize_size=False)
    logger.debug(f"Finished with {final_image}")
    
    # logger.debug(f"About to test pil img")
    # test_pil_img()

    return final_image
