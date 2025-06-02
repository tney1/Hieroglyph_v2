from PIL import ImageEnhance, Image, ImageChops, ImageColor, ImageOps
from PIL.Image import Resampling
import numpy 
import cv2
import math
from deskew import determine_skew

from typing import Union, Tuple
import logging

# 32 pixels is the optimum OCR height
MINIMUM_HEIGHT = 32

logger = logging.getLogger(__name__)


def _set_image_object(photograph):
    """
    :param photograph: System path of a static image on disk

    :return: Returned PIL Object
    """
    target = Image.open(photograph)
    return target


def _extract_statistics(photograph: Image.Image) -> dict:
    """
    :param photograph: An arbritrary image file (e.g., PNG/JPG)

    :return: Dict of the Image Mode (e.g., 1, RGB, CMYK, L), Image Format (e.g., JPEG/PNG), and Dimensions
    """
    return {
        'Mode': photograph.mode,
        'Format': photograph.format,
        'Size': photograph.size
    }


def _set_standard_return(photograph: Image.Image, mod_type: str, factor: float) -> dict:
    """
    :param photograph: An arbritrary image file (e.g., PNG/JPG)

    :return: Dict of the Original Image, Modification Made, Factor Value Used
    """
    return {
        'Path of Original': photograph,
        'Applied Modification': mod_type,
        'Applied Factor': factor
    }


def _manipulate_brightness(photograph: Image.Image, factor: float) -> Image.Image:
    """
    :param photograph: An arbritrary image file (e.g., PNG/JPG)
    :param factor: Percentage adjustment (0.0 = Black Image, 1.0 = Original Image, >=1.0 Increases Brightness)

    :return: PIL Image with the Brightness Adjusted
    """
    output = ImageEnhance.Brightness(photograph)
    output = output.enhance(factor)
    logger.debug(_set_standard_return(photograph, 'Brightness', factor))
    return output


def manipulate_sharpness(photograph: Image.Image, factor: float) -> Image.Image:
    """
    :param photograph: An arbritrary image file (e.g., PNG/JPG)
    :param factor: Percentage adjustment (0.0 = Blurred, 1.0 = Original Image, 2.0 Sharpened)

    :return: PIL Image with the Brightness Adjusted
    """
    output = ImageEnhance.Sharpness(photograph)
    output = output.enhance(factor)
    logger.debug(_set_standard_return(photograph, 'Sharpness', factor))
    return output


def _manipulate_color(photograph: Image.Image, factor: float) -> Image.Image:
    """
    :param photograph: An arbritrary image file (e.g., PNG/JPG)
    :param factor: Percentage adjustment (0.0 = Black & White, 1.0 = Original, Presumably >=1.0 Increased Saturation)

    :return: PIL Image with the Brightness Adjusted
    """
    output = ImageEnhance.Color(photograph)
    output = output.enhance(factor)
    logger.debug(_set_standard_return(photograph, 'Color', factor))
    return output


def _manipulate_contrast(photograph: Image.Image, factor: float) -> Image.Image:
    """
    :param photograph: An arbritrary image file (e.g., PNG/JPG)
    :param factor: Percentage adjustment (0.0 = Solid Gray, 1.0 = Original, >=1.0 to 2.0 Increased Contrast)

    :return: PIL Image with the Brightness Adjusted
    """
    output = ImageEnhance.Contrast(photograph)
    output = output.enhance(factor)
    logger.debug(_set_standard_return(photograph, 'Contrast', factor))
    return output


def _manipulate_inversion():
    raise NotImplementedError()


def _add_padding(photograph: Image.Image, padding: int = 40) -> Image.Image:
    """
    :param photograph: An arbritrary image file (e.g., PNG/JPG)
    :param padding: Number of pixels to add to each side of the image

    :return: PIL Image with added padding
    """
    width, height = photograph.size
    final_width = width + padding*2
    final_height = height + padding*2
    return ImageOps.pad(photograph, (final_width, final_height), color=ImageColor.getcolor("white", photograph.mode))


def manipulate_size(photograph: Union[Image.Image, numpy.ndarray]) -> Union[Image.Image, numpy.ndarray]:
    """Scale image to be at least 32 pixels high for optimal OCR pixel height"""
    if isinstance(photograph, Image.Image):
        if photograph.height < MINIMUM_HEIGHT:
            scale_factor = MINIMUM_HEIGHT / photograph.height
            logger.debug(f"Scaling {photograph} by {scale_factor} to hit {MINIMUM_HEIGHT} as it is currently"
                         f" ({photograph.size})-> {(int(photograph.width * scale_factor), int(photograph.height * scale_factor))}")
            return photograph.resize(
                (int(photograph.width * scale_factor), int(photograph.height * scale_factor)),
                Resampling.LANCZOS
            )
        else:
            # NOTE: Could scale down as well, might help with large font
            return photograph
    elif isinstance(photograph, numpy.ndarray):
        height, width = photograph.shape[0], photograph.shape[1]
        if height < MINIMUM_HEIGHT:
            scale_factor = MINIMUM_HEIGHT / height
            new_dimensions = (int(width * scale_factor), int(height * scale_factor))
            logger.debug(f"Scaling {photograph.shape} by {scale_factor} to hit {MINIMUM_HEIGHT} as it is"
                         f" currently {(width, height)}-> {new_dimensions}")
            return cv2.resize(
                photograph,
                new_dimensions,
                interpolation=cv2.INTER_NEAREST
            )
        else:
            # NOTE: Could scale down as well, might help with large font
            return photograph
    else:
        print(f"ERROR: Invalid photograph type: {type(photograph)}")

# Additional Image processing steps
def normalize_image(image: numpy.ndarray) -> numpy.ndarray:
    norm_img = numpy.zeros((image.shape[0], image.shape[1]))
    return cv2.normalize(image, norm_img, 0, 255, cv2.NORM_MINMAX)

def rotate(image: numpy.ndarray, angle: float, background: Union[int, Tuple[int, int, int]]) -> numpy.ndarray:
    # convert to greyscale here so that it ...  

    old_width, old_height = image.shape[:2]
    angle_radian = math.radians(angle)
    width = abs(numpy.sin(angle_radian) * old_height) + abs(numpy.cos(angle_radian) * old_width)
    height = abs(numpy.sin(angle_radian) * old_width) + abs(numpy.cos(angle_radian) * old_height)
    image_center = tuple(numpy.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    rot_mat[1, 2] += (width - old_width) / 2
    rot_mat[0, 2] += (height - old_height) / 2
    return cv2.warpAffine(image, rot_mat, (int(round(height)), int(round(width))), borderValue=background)

# def set_image_dpi(image: Image.Image) -> Image.Image: # same as manipulate_size
#     length_x, width_y = image.size
#     factor = min(1, float(1024.0 / length_x))
#     size = int(factor * length_x), int(factor * width_y)
#     im_resized = image.resize(size, Image.ANTIALIAS)
#     temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
#     temp_filename = temp_file.name
#     im_resized.save(temp_filename, dpi=(300, 300))
#     return Image.open(temp_filename)

def remove_noise(image: numpy.ndarray) -> numpy.ndarray:
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 15)

def thinning(image: numpy.ndarray) -> numpy.ndarray: # more useful for handwritten text to widen and make the line-width uniform. Not good for pages with various fonts/sizes
    kernel = numpy.ones((5, 5), numpy.uint8)
    return cv2.erode(image, kernel, iterations=1)

def get_grayscale(image: numpy.ndarray) -> numpy.ndarray: 
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def thresholding(image: numpy.ndarray) -> numpy.ndarray:
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]



# TODO: Validate Values (Path, Factor Input, Output Path)
def execute_enhancement_on_pil_img(input_pil: Image.Image) -> Image.Image:
    """
    Applies Modifications to PIL Image and Applied Outcomes of Each Iteration in Memory (Not Disk)

    :param input_pil: A PIL Image

    :return: PIL Image with All Adjustments
    """


   
    # Convert PIL Image to numpy array for OpenCV processing
    image_array = numpy.array(input_pil)



    # image_array = normalize_image(image_array)

    image_array = remove_noise(image_array)
    image_array = get_grayscale(image_array)
    angle = determine_skew(image_array)
    image_array = rotate(image_array, angle, (0,0,0))
    # image_array = thresholding(image_array) # threshold the individual boxes in boxes.py
    # image_array = thinning(image_array) 
    # Convert back to PIL Image
    processed_pil = Image.fromarray(image_array)
    

    brightness_output = _manipulate_brightness(processed_pil, 1.1) # processed_pil or input_pil if skipping first processing steps
    color_output = _manipulate_color(brightness_output, 1.5)
    contrast_output = _manipulate_contrast(color_output, 1.5)
    resized_output = manipulate_size(contrast_output)
    sharpened_output = manipulate_sharpness(resized_output, 1.0) # 2 is most sharp
    # final_modified_image = _add_padding(sharpened_output)
    # return final_modified_image
    return sharpened_output


def test_pil_img():
    input_path = 'assets/diagrams/table.png'  # Input to Convert to PIL Image  #3_zh_sample_b2_d4.jpeg
    output_path = 'assets/diagrams/table.enhanced.both.png'  # Output Path
    pil_conversion = Image.open(input_path)  # Turns 'test_image' to PIL Image
    modified_img = execute_enhancement_on_pil_img(pil_conversion)  # Returned Manipulated PIL
    modified_img.save(output_path, quality=95, dpi=(300, 300))
    input_path = 'assets/diagrams/ss.png'  # Input to Convert to PIL Image  #3_zh_sample_b2_d4.jpeg
    output_path = 'assets/diagrams/ss.enhanced.both.png'  # Output Path
    pil_conversion = Image.open(input_path)  # Turns 'test_image' to PIL Image
    modified_img = execute_enhancement_on_pil_img(pil_conversion)  # Returned Manipulated PIL
    modified_img.save(output_path, quality=95, dpi=(300, 300))
    input_path = 'assets/diagrams/skew.png'  # Input to Convert to PIL Image  #3_zh_sample_b2_d4.jpeg
    output_path = 'assets/diagrams/skew.enhanced.both.png'  # Output Path
    pil_conversion = Image.open(input_path)  # Turns 'test_image' to PIL Image
    modified_img = execute_enhancement_on_pil_img(pil_conversion)  # Returned Manipulated PIL
    modified_img.save(output_path, quality=95, dpi=(300, 300))
def test_manipulate_size():
    input_path = 'assets/diagrams/small-text.png'  # Input to Convert to array
    output_path_array = 'assets/diagrams/small-text-resized-array.png'  # Output Path
    output_path_pil = 'assets/diagrams/small-text-resized-pil.png'  # Output Path

    image_array = cv2.imread(input_path)  # Turns 'test_image' to array
    modified_array = manipulate_size(image_array)  # Returned Manipulated array
    cv2.imwrite(output_path_array, modified_array)

    pil_conversion = Image.open(input_path)  # Turns 'test_image' to PIL Image
    modified_pil = manipulate_size(pil_conversion)  # Returned Manipulated PIL
    modified_pil.save(output_path_pil, quality=95, dpi=(300, 300))


if __name__ == "__main__":
    test_pil_img()
    test_manipulate_size()

