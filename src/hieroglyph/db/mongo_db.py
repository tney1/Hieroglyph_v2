import pymongo
import logging
from bson.json_util import dumps, loads, RELAXED_JSON_OPTIONS, CANONICAL_JSON_OPTIONS
from pathlib import Path
from os import getenv

logger = logging.getLogger(__name__)


def _connect_to_mongo():

    logger.debug("Fetching MongoDB Credentials and Location from Compose File")

    # Get Environment Variables from Docker Compose File
    MONGO_USR = Path(getenv("MONGO_USR"))
    MONGO_PWD = Path(getenv("MONGO_PWD"))
    MONGO_IP = Path(getenv("MONGO_IP"))
    MONGO_PORT = Path(getenv("MONGO_PORT"))

    # Connect to MongoDB with Environment Variables
    try:
        mongo_connection_string = f"{MONGO_USR}:{MONGO_PWD}@{MONGO_IP}:{MONGO_PORT}"
        conn = pymongo.MongoClient(f'mongodb://{mongo_connection_string}/')
        db_target = conn["ui_session_tests"]
        column_target = db_target["page_data"]
    except Exception as e:
        return {f"Error with Mongo Connection: {e}"}

    return column_target


def _check_db_if_hash_already_exists(hashkey: str):
    """
    Checks if a document page is already in the database.
    If the hash is in the database, return True.
    If the hash is not in the database, return False.

    :param hashkey: String value of a SHA-256 hash
    :returns: True/False Boolean
    """

    column_target = _connect_to_mongo()
    logger.debug(f'Checking if ({hashkey}) already exists...')
    find = column_target.find_one({"src_hash": hashkey})
    returned_find = dumps(find, sort_keys=True, ensure_ascii=False)

    if returned_find == "null":
        return False
    else:
        return True
