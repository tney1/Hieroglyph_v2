import logging
from base64 import b64decode, b64encode
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional, Union

import cv2
import numpy as np
from PIL import Image

from hieroglyph.process.enhance import manipulate_size, manipulate_sharpness
from hieroglyph.general import INBOUND_IMAGE_TYPE

logger = logging.getLogger(__name__)


class ImageWrapper:
    """
    Wrapper class over a np.array, Pillow Image, name, and bounding box for an image
    {
        name: "" # image name
        image_type: Enum # Image type, text or diagram
        _array: np.array() # Numpy array representing the Image,
        _pillow: PIL.Image.Image # Pillow Image (lazy create to provide certain functionality like enhance/rotate/resize/save),
        _box: [x,y,w,h] # bounding box for the image, if it was originally part of a larger image
        _uninitialized: bool # Status of initialization of _array
    }
    """
    __slots__ = ("_array", "_pillow", "_box", "_uninitialized", "image_type", "name")

    def __init__(self, src_image: Union[str, Image.Image, np.ndarray], image_type: INBOUND_IMAGE_TYPE,
                 name: Optional[str], box: Optional[List[float]] = None, normalize_size: bool = False):
        self.image_type: INBOUND_IMAGE_TYPE = image_type
        self._box: list | None = box if box else None
        self._pillow: Image.Image | None = None
        if not name:
            raise ValueError("Must provide image object and name")
        elif isinstance(src_image, str):
            # logger.debug(f"Converting {name} from base64")
            self.from_base64(src_image, name)
            self.manipulate_source_image_size()
            self.manipulate_source_image_sharpness()
        elif isinstance(src_image, Image.Image):
            # logger.debug(f"Converting {name} from pillow")
            self.from_pillow(src_image, name)
        elif isinstance(src_image, np.ndarray):
            # logger.debug(f"Converting {name} from numpy array")
            self.from_array(src_image, name)
        else:
            self._uninitialized: bool = True
        if normalize_size:
            self.manipulate_source_image_size()

    def manipulate_source_image_sharpness(self):
        """Sharpen image"""
        self.update(manipulate_sharpness(self.get_pillow(), factor=1.7))

    def manipulate_source_image_size(self):
        """Resize the image to an appropriate dimension for OCR"""
        self.update(manipulate_size(self.get_array()))

    def from_base64(self, src_b64image: str, name: str):
        image_fp = NamedTemporaryFile("wb+")
        image_fp.write(b64decode(src_b64image))
        image_fp.seek(0)
        img = Image.open(image_fp)
        img_arr = np.array(img)
        image_fp.close()
        self._array: np.ndarray = cv2.cvtColor(img_arr, cv2.COLOR_BGR2GRAY) if len(img_arr.shape) == 3 else img_arr
        self.name: str = name
        self._uninitialized = False

    def from_array(self, src_array: np.ndarray, name: str):
        self._array = cv2.cvtColor(src_array, cv2.COLOR_BGR2GRAY) if len(src_array.shape) == 3 else src_array.copy()
        self.name = name
        self._uninitialized = False

    def from_pillow(self, src_pillow: Image.Image, name: str):
        img_arr = np.array(src_pillow)
        self._array = cv2.cvtColor(img_arr, cv2.COLOR_BGR2GRAY) if len(img_arr.shape) == 3 else img_arr
        self.name = name
        self._uninitialized = False

    def to_base64(self) -> str:
        if self._uninitialized:
            raise ValueError("Image is uninitialized, illegal operation attempted")
        if not self._pillow:
            self._pillow = Image.fromarray(self._array)
        return b64encode(self._pillow.tobytes()).decode("utf-8")

    def to_array(self) -> np.ndarray:
        if self._uninitialized:
            raise ValueError("Image is uninitialized, illegal operation attempted")
        return self._array.copy()

    def to_pillow(self) -> Image.Image:
        if self._uninitialized:
            raise ValueError("Image is uninitialized, illegal operation attempted")
        if self._pillow:
            return self._pillow.copy()
        else:
            return Image.fromarray(self._array)

    def get_array(self) -> np.ndarray:
        if self._uninitialized:
            raise ValueError("Image is uninitialized, illegal operation attempted")
        return self._array

    def get_pillow(self) -> Image.Image:
        if self._uninitialized:
            raise ValueError("Image is uninitialized, illegal operation attempted")
        if self._pillow:
            return self._pillow
        else:
            self._pillow = Image.fromarray(self._array)
            return Image.fromarray(self._array)

    def update(self, new_data: Union[str, Image.Image, np.ndarray], name: str = ""):
        """Update internal objects to save space"""
        self.name = name if name else self.name
        if isinstance(new_data, str):
            image_fp = NamedTemporaryFile("wb+")
            image_fp.write(new_data)
            image_fp.seek(0)
            img_arr = np.frombuffer(image_fp)
            image_fp.close()
            self._array = cv2.cvtColor(img_arr, cv2.COLOR_BGR2GRAY) if len(img_arr.shape) == 3 else img_arr
            self._pillow = Image.fromarray(self._array) if self._pillow else None
        elif isinstance(new_data, np.ndarray):
            self._array = cv2.cvtColor(new_data, cv2.COLOR_BGR2GRAY) if len(new_data.shape) == 3 else new_data
            self._pillow = Image.fromarray(self._array) if self._pillow else None
        elif isinstance(new_data, Image.Image):
            img_arr = np.array(new_data)
            self._array = cv2.cvtColor(img_arr, cv2.COLOR_BGR2GRAY) if len(img_arr.shape) == 3 else img_arr
            self._pillow = Image.fromarray(self._array) if self._pillow else None
        else:
            raise ValueError(f"Invalid update data type: {new_data.__class__}")
        return self

    def save(self, filename: Union[str, Path]):
        """Save image out to filename"""
        if self._pillow:
            self._pillow.save(str(filename), quality=95, subsampling=0)
        else:
            cv2.imwrite(str(filename), self._array)

    def __str__(self) -> str:
        return f"<ImageWrapper {self.name=}, {self._uninitialized=}," + \
               f" pillow={self._pillow.info if self._pillow else self._pillow}," + \
               f" array={'exists' if len(self._array) else 'does not exist'}," + \
               f" box={self._box if self._box else 'none'}>"

    def __hash__(self):
        return hash((np.array2string(self._array), self._box, self.name, self._uninitialized))

    def __eq__(self, o) -> bool:
        return self._array == o._array and self._box == o._box and \
            self.name == o.name and self._uninitialized == self._uninitialized

    __repr__ = __str__
