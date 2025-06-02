import cv2
import numpy as np
from PIL import Image
import logging
logger = logging.getLogger(__name__)


def median_blur(source_image: np.ndarray) -> np.ndarray:
    """ Add a slight blur to the image to help reduce noise """
    return cv2.medianBlur(source_image, 3)


# Return the grayscale version of the image
def grayscale_image(source_image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(source_image, cv2.COLOR_RGB2GRAY)


def global_threshold(source_image: np.ndarray) -> np.ndarray:
    """Return the Global Thresholding (v=127) version of the image"""
    ret, modified_image_array = cv2.threshold(source_image, 127, 255, cv2.THRESH_BINARY)
    return modified_image_array


def mean_threshold(source_image: np.ndarray) -> np.ndarray:
    """Return the Adaptive Mean Thresholding version of the image"""
    return cv2.adaptiveThreshold(source_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)


def gaussian_threshold(source_image: np.ndarray) -> np.ndarray:
    """Return the Adaptive Gaussian Thresholding version of the image"""
    return cv2.adaptiveThreshold(source_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)


def threshold_image(source_image: np.ndarray, method=None) -> np.ndarray:
    """Primary transform input function with source input image being a Pillow Image object"""
    if method:
        modified_array = method(source_image)
        return modified_array
    else:
        logger.debug("Threshold: Returning unmodified image")
        return source_image
