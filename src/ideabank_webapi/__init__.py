"""
    :module_name: ideabank_webapi
    :module_summary: An API for the services utilized by the Idea Bank application
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

from typing import Union
import logging
import time
import threading

from fastapi import FastAPI

app = FastAPI()

LOGGER = logging.getLogger(__name__)
LOG_HANDLER = logging.StreamHandler()
LOG_FORMAT = logging.Formatter(
        fmt='[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %z'
        )
LOGGER.setLevel(logging.DEBUG)
LOG_HANDLER.setLevel(logging.DEBUG)
LOG_HANDLER.setFormatter(LOG_FORMAT)
LOGGER.addHandler(LOG_HANDLER)


@app.get("/")
def read_root():
    time.sleep(3)
    LOGGER.info(f"Request being handled by Thread#{threading.get_native_id()}")
    LOGGER.info("Respond to root resource")
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    LOGGER.info("Respond to items resource")
    if not q:
        LOGGER.warning("query parameter q not defined")
    return {"item_id": item_id, "q": q}
