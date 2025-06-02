import os
import json
import logging

from hieroglyph.general import internal_language_mapping

logger = logging.getLogger(__name__)


def get_model_details(model_dir, init_source_lang):
    if not os.path.exists(model_dir):
        logger.error("Specified language model directory does not exist")
        return None

    logger.info(f"Identifying available models: {model_dir}")
    model_details = {}
    for model_name in os.listdir(model_dir):
        model_path = os.path.join(model_dir, model_name)
        if not os.path.isdir(model_path):
            logger.debug(f"File {model_name} is not a directory, skipping.")
        elif not os.path.exists(os.path.join(model_path, "config.json")):
            logger.debug(f"File config.json not found in {model_name}, skipping.")
        else:
            logger.debug(f"Evaluating model with name: {model_name}")
            # Identify the model type for which UI element it should be on
            with open(model_path + "/config.json", "r") as inf:
                config = json.load(inf)
            if config["architectures"][0] != "MarianMTModel":
                logger.debug("Not a language model, continuing to next model")
                continue

            with open(os.path.join(model_path, "tokenizer_config.json"), "r") as tokenizer_file:
                model_config_file = json.load(tokenizer_file)

            source_lang = internal_language_mapping(model_config_file["source_lang"]).to_translate()
            target_lang = internal_language_mapping(model_config_file["target_lang"]).to_translate()

            if source_lang != init_source_lang or target_lang != "en":
                logger.debug("Model language missmatch, continuing to next model")
                continue

            model_details = {"name": model_name,
                             "source_lang": source_lang,
                             "target_lang": target_lang,
                             "path": model_path}
            logger.info(f"Valid language model located: {model_name}")
            break
    return model_details
