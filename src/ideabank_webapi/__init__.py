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

from .handlers.creators import AccountCreationHandler
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


@app.post("/accounts/create",)
def create_account(
        new_account: CredentialSet,
        response: Response
        ):
    """Create a new account with the given display name and password if available"""
    handler = AccountCreationHandler()
    handler.use_service(RegisteredService.ACCOUNTS_DS, AccountsDataService())
    handler.receive(new_account)
    response.status_code = handler.result.code
    return handler.result
