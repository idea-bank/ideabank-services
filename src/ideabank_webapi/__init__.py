"""
    :module_name: ideabank_webapi
    :module_summary: An API for the services utilized by the Idea Bank application
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

from typing import Union
import logging
import time
import threading

from fastapi import FastAPI, Response

from .handlers.creators import AccountCreationHandler, AccountCreationRequest
from .models.artifacts import CredentialSet
from .services import RegisteredService, AccountsDataService

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
    """Default endpoint"""
    time.sleep(3)
    LOGGER.info(
            "Request being handled by Thread#%s",
            str(threading.get_native_id())
        )
    LOGGER.info("Respond to root resource")
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q_param: Union[str, None] = None):
    """Endpoint with path and query parameter"""
    LOGGER.info("Respond to items resource")
    if not q_param:
        LOGGER.warning("query parameter q not defined")
    return {"item_id": item_id, "q_param": q_param}


@app.post("/accounts/create",)
def create_account(
        new_account: CredentialSet,
        response: Response
        ):
    """Create a new account with the given display name and password if available"""
    handler = AccountCreationHandler()
    handler.use_service(RegisteredService.ACCOUNTS_DS, AccountsDataService())
    handler.receive(AccountCreationRequest(
        method='POST',
        resource='/accounts/create',
        new_account=new_account
        ))
    response.status_code = handler.result.code
    return handler.result
