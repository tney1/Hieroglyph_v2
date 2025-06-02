import multiprocessing
from enum import Enum
import re


# MAX_WORKERS = cpu_count - 1 if (cpu_count := multiprocessing.cpu_count()) > 1 else cpu_count
MAX_WORKERS = 4


# Enum Type
# This enumerator assists with signaling to the pipeline which
# thresholding technique should be used for primarily 
# diagram-based documents and text-based documents
class INBOUND_IMAGE_TYPE(Enum):
    DIAGRAM_BASED = "diagram"
    TEXT_BASED = "text"
    TEXT_BASED_LINES = "text_lines"
    TABLE_BASED = "table"


# Assists with the conversion of human-readable language tags
# such as 'Chinese' to the tags required for the pipeline such as 'chi_sim' or 'zho'
# and 'English' to 'eng' or 'en as appropriate
class internal_language_mapping():

    def __init__(self, input_lang):
        self.input_lang = str(input_lang).strip().lower()
        # self.shortcode = input_lang[:3]

    def to_ocr(self):
        match self.input_lang:
            case "chi" | "zho" | "chinese":
                return "chi_sim+chi_tra"
            case "simp_chinese":
                return "chi_sim"
            case "trad_chinese":
                return "chi_tra"            
            case "ru" | "rus" | "russian":
                return "rus"
            case "en" | "eng" | "english":
                return "eng"
            case _:
                raise Exception(f"Unsupported language: {self.input_lang}")

    def to_translate(self):
        match self.input_lang:
            case "chinese" | "chi_sim+chi_tra" | "zho" | "chinese":
                return "zho"
            case "chi_sim":
                return "zho"
            case "chi_tra":
                return "zho"  
            case "ru" | "rus" | "russian":
                return "ru"
            case "en" | "eng" | "english":
                return "en"
            case _:
                raise Exception(f"Unsupported language: {self.input_lang}")