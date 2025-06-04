import pytesseract
from PIL import Image
from typing import List, Tuple

def extract_sentences_with_boxes(box_img: Image.Image) -> List[Tuple[str, Tuple[int, int, int, int]]]:
    """
    Given a cropped paragraph image, return sentence segments with their bounding boxes.
    """
    data = pytesseract.image_to_data(box_img, output_type=pytesseract.Output.DICT)
    sentences = []
    current_sentence = ""
    current_coords = []

    for i in range(len(data['text'])):
        word = data['text'][i]
        if not word.strip():
            continue

        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        current_sentence += word + " "
        current_coords.append((x, y, x + w, y + h))

        if word.strip()[-1] in ".!?":
            xs = [c[0] for c in current_coords]
            ys = [c[1] for c in current_coords]
            x2s = [c[2] for c in current_coords]
            y2s = [c[3] for c in current_coords]
            x_min, y_min = min(xs), min(ys)
            x_max, y_max = max(x2s), max(y2s)
            sentences.append((current_sentence.strip(), (x_min, y_min, x_max - x_min, y_max - y_min)))
            current_sentence = ""
            current_coords = []

    return sentences
