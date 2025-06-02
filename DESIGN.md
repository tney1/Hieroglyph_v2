# Script Pad Design

The following discusses design choices and system architecture explanations for Script Pad repository.

## Difference Between Thresholding Techniques

Why did we choose to use global thresholding? = Great job at box detection, we only use it for box detection

Why did we remove gaussian and mean thresholding? = Too busy and messy

Why do we use grayscale in combination with the box detection from global? = Grayscale does best with adaptiveThresholding, which we use to 

### Why Not Use Tesseract for Bounding Box Detection?

Reference: `./scripts/test-tesseract.py`

`pytesseract` offers multiple language-specific, pre-trained models for bounding box detection. To validate pytesseract for text-bounding in comparison to the current OpenCV-centric hybrid pipeline, a basic script (`./scripts/test-tesseract.py`) was used to process the following a snippet of a text-based Huawei image: `./assets/diagrams/Huawei_NetEco_Pg1_Text-1.png` using the Tesseract Chinese Simplified model (`sudo apt-get install tesseract-ocr-chi-sim`).

The raw bounding results can be found at the following location: `./assets/diagrams/Example_Tesseract_Only_Bounding.png`. In summary, bounding of Chinese Simplified characters was found to be incosistent with scattered blocks of individual and grouped characters. Inconsistencies in bounding increased as characters became smaller.

Open-source documentation and code indicates bounding results can be improved, but all improvements rely on OpenCV-based thresholding, dilation, and miscellaneous manipulation methods -- Effectively negating the value of raw `pytesseract`-based bounding and offering no clear advantages over the current pipeline and bounding techniques. As a result, `pytesseract` bounding was not pursued further.
