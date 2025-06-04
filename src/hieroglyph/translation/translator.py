import os
import json
import torch
import logging
import Levenshtein
from enum import Enum
from pathlib import Path
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM

import hieroglyph.translation.utils as utils
from hieroglyph.general import internal_language_mapping

logger = logging.getLogger(__name__)

"""
This is the typical max_sentence_length for MarianMT models.
Only used as a default if not specified in a model's config
    TRANSLATE_LIMIT = 512  # PARTIAL LOSS OF RESULTS
    TRANSLATE_LIMIT = 256  # MINOR LOSS OF RESULTS
    TRANSLATE_LIMIT = 128  # BEST RESULTS
"""
TRANSLATE_LIMIT = 128  # BEST RESULTS


class Translator(object):
    """
    Using MarianMT language translation models, translate user specified text in a configured source language
    to the target language, english.
    """
    def __init__(self):
        self.models_dir = None
        self.source_language = None
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.model_loaded = False
        self.model = None
        self.tokenizer = None

    def configure(self, models_dir, language):
        """
        Configure the translator by providing the necessary information for model identification.

        :param models_dir: Filesystem directory containing all available langauage models
        :param language: Source language for the model to load
        """
        self.models_dir = models_dir
        # Converts Russian to ru and Chinese to zho
        self.source_language = internal_language_mapping(language).to_translate()
        logger.info(f"Translator configured with language of '{language}' ('{self.source_language}')"
                    f" and models path of '{self.models_dir}'")

    def setup(self):
        """
        Identify the correct model, based on configuration. If a valid model is identified, load the model for use.
        """
        model = utils.get_model_details(model_dir=self.models_dir, init_source_lang=self.source_language)
        if model:
            self.load_model(model)
        else:
            logger.error(f"No valid language model found for desired language: {self.source_language}")

    def load_model(self, model_details):
        """
        Load the identified translation model into memory for use, set the model and tokenizer variables
        in the translator for use during the translation process.

        :param model_deails: Dictionary containing information about the model and its location on the filesystem
        """
        if os.path.exists(model_details["path"]):
            logger.info(f"Loading {model_details['name']} as translator...")

            logger.info(f"Before LOADING the model, setting torch device to '{self.device}'.")
            logger.info(f"According to torch, the state of available GPUs is: {torch.cuda.is_available()}")
            # Checking All Devices
            for i in range(torch.cuda.device_count()):
                logger.info(f"According to the system, {torch.cuda.get_device_properties(i).name} is available!")
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_details["path"]).to(self.device)
            self.tokenizer = AutoTokenizer.from_pretrained(model_details["path"])
            self.model_loaded = True
            logger.info(f"Loaded {model_details['name']}")
        else:
            logger.error(f"Model path {model_details['path']} isn't a valid path.")

    def translate(self, lang_in="zho", lang_out="en", text="") -> list:
        """
        Translate user provide source text from the lang_in to the lang_out.

        :param lang_in: Source language of the text (must match self.source_language set on configuration)
        :param lang_out: Target language for translation result (english)
        :param text: List of foreign source text for translation
        :returns: Translation of text to return to the user
        """
        # This does a lot of data handling work for older translation models, which is probably not needed anymore
        # with stuff like sentencepiece being popular, so I'd recommend using a more modern approach

        logger.debug(f"Translation Request: {lang_in} -> {lang_out}: {text}.")

        lang_in = internal_language_mapping(lang_in).to_translate()

        if not text:
            logger.error("No text specified for translation")
            return None
        if not self.model_loaded:
            logger.error("No suitable tranlation model loaded")
            return None
        if lang_in != self.source_language:
            logger.error("Translation requested for language not matching configured source language")
            return None

        # Set the incoming text string to a list
        incoming_text = [text]

        # Tokenize and retrieve the attention mask of incoming text
        tokenized_text = self.tokenize_incoming_text(incoming_text)

        # We sum each row in the tensor object (a numpy ndarray) e.g., [303, 153, ...]
        sum_of_token_lengths = [int(sum(x)) for x in tokenized_text]

        # Extracts the largest value in the list of sums
        max_sum_of_token_lengths = max([int(sum(x)) for x in tokenized_text])

        logger.debug(f'Out of {len(tokenized_text)} entries in the text'
                     f' calculated token size(s) of {sum_of_token_lengths}.')
        logger.debug(f'Assessing largest sum token {max_sum_of_token_lengths}'
                     f' against the limit of {TRANSLATE_LIMIT} tokens per entry.')

        # While any of the sums in the list are more than TRANSLATE_LIMIT (128) keep looping
        while max([int(sum(x)) for x in tokenized_text]) > TRANSLATE_LIMIT:

            # Take the incoming_text list and apply the algo to trim it down
            divided_text = self.shrink_text_to_reduce_tokens(incoming_text)

            # Using the new list with the divided text, tokenize it again, and run the loop again
            # to check whether any of the summed tokens are more than TRANSLATE_LIMIT
            tokenized_text = self.tokenize_incoming_text(divided_text)

        new_sum_of_token_lengths = [int(sum(x)) for x in tokenized_text]
        logger.debug(f'Previous token sums were {sum_of_token_lengths} new sums are {new_sum_of_token_lengths}')

        translated_text = self.decode_completed_translation_data(incoming_text)
        logger.debug(f'Returning the final result to the user, see below: \n {translated_text}')

        return translated_text

    def tokenize_incoming_text(self, text):
        """
        Takes a list of strings (however long that may be) tokenizes it, and returns the attention mask
        of the tokenized text. The attention mask is a numpy ndarray where each row corresponds to a list
        entry from the provided string. Both the tokenized text and the attention mask are tensor objects.

        :param text: List of foreign source text for translation
        :returns: The attention mask of the tokenized text, i.e., a tensor object consisting of a numpy ndarray
        """
        tokenized = self.tokenizer(text, return_tensors="pt", padding=True).to(self.device)
        attention_mask_of_tokens = tokenized["attention_mask"]

        return attention_mask_of_tokens

    def shrink_text_to_reduce_tokens(self, incoming_text):
        """
        This process essentially rebuilds the original list (while preserving all content) into a list
        of strings that all have a sum token value at or below the TRANSLATE LIMIT. Takes a list of text
        entries and the TRANSLATE_LIMIT constant to break any strings that violate the TRANSLATE_LIMIT
        threshold into two or more entries.
        E.g., ['really really long string'] becomes ['really really', 'long string']

        :param incoming_text: List of foreign source text for translation
        :return: New list with divided and chunked foreign source text
        """

        # We set longest_str to our identified index of the longest string of text in incoming_text
        # We then proceed to get the index of the longest string in incoming_text
        longest_str = max(incoming_text, key=len)
        lengthy_text_idx = incoming_text.index(longest_str)

        logger.debug(f'Longest string identified at index position {lengthy_text_idx}.')

        # We then figure out how to split the longest string into a series of individual words
        # This is language specific! For example below is a Chinese-centric set of characters
        # split_char = "。" if "。" in longest_str else "，" if "，" in longest_str else None
        split_char = self.determine_split_character(longest_str)

        if split_char:
            logger.debug(f"Splitting text on the '{split_char}' character...")
            words = longest_str.split(split_char)
        else:
            logger.debug(f'No split characters were found, splitting words in half.')
            words = longest_str.split()

        # We now identify the halfway point of our words
        try:
            half = len(words) // 2
            logger.debug(f'Halfway point equated to: {half}')

            # If there is no halfway point we have to cut the sentence in half and hope for a reasonable translation
            if half == 0:
                logger.debug(f'No halfway point found in entry, must divide in half to avoid race condition.')
                logger.debug('Warning - Arbritrarily dividing a string and this can potentially impact translation.')

                plaintext = words[0]
                logger.debug(f'Preparing the following text for division: {plaintext}')

                # Splits the String in Half, Takes Care of Odd Number of Characters
                first_half, second_half = plaintext[:len(plaintext) // 2], plaintext[len(plaintext) // 2:]
                incoming_text[lengthy_text_idx] = ''.join(first_half)
                incoming_text.insert(lengthy_text_idx + 1, ''.join(second_half))

            # Otherwise we can continue as normal and neatly divide the text by any identified split characters
            else:
                logger.debug(f'Found a halfway point in provided text. Proceeding...')
                # We then set our previously identified longest string to our now trimmed words
                # The string now consists of all words /after/ the index position of the "halfway point"
                incoming_text[lengthy_text_idx] = ''.join(words[:half])

                # We staple the remaining words /prior/ to the halfway point to the index position thats +1
                incoming_text.insert(lengthy_text_idx + 1, ''.join(words[half:]))

        except Exception as e:
            logger.error(f"Exception occured: {e}")
            raise ValueError(f"Unexpected error. This may be due to no halfway point in the words variable: {words}")

        return incoming_text

    def determine_split_character(self, longest_string):
        """
        Takes a string and identifies the presence of any 'split characters', characters that mark
        a potential seperation point to divide the string into two or more pieces.

        :param longest_string: A single string of text
        :return: The character to use in the parent function to split the string into two or more parts
        """
        match self.source_language:
            case "zho" | "chi_sim+chi_tra":  # Chinese
                split_characters = ["。", "，", "一", ";", ",", ":", "(", ")", "-", ".", "[", "]", '"']
            case "ru" | "rus":  # Russian
                # TODO: Need to Add More Russian Characters Based on Document Testing
                split_characters = [".", "?", "!", "«", "»", "„", "“", "—", "-", ",", ":", ";", "(", ")", "[", "]", '"']
            case _:  # Backup Technique Using English Punctuation
                logger.error(f'Could not find a list of split characters to use for dividing text'
                             f' for the {self.source_language} language')
                logger.debug('Attempting to use English-based punctuation to split characters as a backup...')
                split_characters = [".", "!", "?", ",", "一", ";", ":", "(", ")", "-", "—", "[", "]", '"']

        # For each character in the split_characters list, check if the longest_string contains the character
        # If it does contain the character immediately return it as the new 'split character'. Otherwise return None.
        for character in split_characters:
            if character in longest_string:
                return character
        return None

    def decode_completed_translation_data(self, processed_text):
        """
        The final step before returning data to the user, decodes the tokenized text into the
        destination language (effectively translates text), and turns it into a single list entry

        :param processed_text: List of foreign source text for translation after splitting and chunking
        :returns: Translated data to return to the user
        """
        tokenized = self.tokenizer(processed_text, return_tensors="pt", padding=True).to(self.device)

        translated = self.model.generate(**tokenized, max_new_tokens=TRANSLATE_LIMIT)
        decoded_text = [self.tokenizer.decode(t, skip_special_tokens=True) for t in translated]

        combined_text = str()
        for entry in decoded_text:
            combined_text += str(entry)

        return [combined_text]

from hieroglyph.utils.sentence_segmentation import extract_sentences_with_boxes
from PIL import Image
from typing import List, Tuple

def translate_sentences_from_box(box_img: Image.Image, source_lang: str, target_lang: str) -> List[Tuple[str, str, Tuple[int, int, int, int]]]:
    """
    Translates each sentence extracted from an image region (paragraph box) and returns:
    (original sentence, translated sentence, bounding box)
    """
    translator = Translator()
    translator.configure(models_dir="", language=source_lang)  # You may want to set a real path and call .setup()
    translator.setup()

    results = []
    for sentence, (x, y, w, h) in extract_sentences_with_boxes(box_img):
        try:
            translated = translator.translate(source_lang, target_lang, sentence)
        except Exception as e:
            translated = [f"[Translation Error: {e}]"]

        results.append((sentence, translated[0], (x, y, w, h)))

    return results


if __name__ == "__main__":

    logging.basicConfig(handlers=[logging.StreamHandler()],
                        format="%(levelname)s: [%(module)s] %(message)s",
                        level=logging.INFO)

    logging.info("Translator CLI testing")

    # Terrible pathing, but navigates to project base directory from current location of this file
    base_dir = Path(os.path.abspath(__file__)).parent.parent.parent.parent
    models_dir = os.path.join(base_dir, "models")

    translator = Translator()
    translator.configure(models_dir, "chinese")
    translator.setup()

    sample_txt = "Hello how are you today? The weather is nice outside, it is bright and sunny." \
                 " How is your cofee. It is delicious, this shop makes a great espresso. Is the" \
                 " pastry good as well? Yes, the apple pastry is just like my grandma made," \
                 " so buttery and flakly."
    resp = translator.translate(lang_in='eng', lang_out='zho', text=sample_txt)
    if resp:
        print(resp[0])

    chinese_sample = "你好，今天怎么样？ 外面天气很好，阳光明媚。 你的咖啡怎么样。 很好吃，这家店的浓缩咖啡很棒。" \
                     " 糕点也好吃吗？ 是的，苹果糕点就像我奶奶做的一样，黄油味十足，酥脆。"
    resp2 = translator.translate(lang_in='zho', lang_out='en', text=chinese_sample)
    if resp2:
        print(resp2)
