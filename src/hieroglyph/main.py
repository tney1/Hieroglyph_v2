import sys
import uvicorn
import argparse
import logging
from pathlib import Path
from os import getenv

from hieroglyph.api import app, translator
from hieroglyph.utils import get_log_level

log_level = get_log_level(getenv("LOG_LEVEL", "DEBUG"))

logging.basicConfig(handlers=[logging.StreamHandler()],
                    format="%(levelname)s: [%(module)s] %(message)s",
                    level=log_level)

logger = logging.getLogger(__name__)

initial_port = int(getenv("INIT_PORT", "8088"))
number_of_workers = int(getenv("WORKER_COUNT", "4"))
initial_language = getenv("INIT_LANG", "chinese")
model_dir = Path(getenv("MODEL_DIR", "/models"))

if initial_port not in range(0, 65535):
    print(f"error: provided port number not in range 0-65535: '{initial_port}'")
    sys.exit()

translator.configure(models_dir=model_dir, language=initial_language)

translator.setup()

if __name__ == '__main__':
    uvicorn.run("__main__:app", host="0.0.0.0", port=initial_port, workers=number_of_workers)
