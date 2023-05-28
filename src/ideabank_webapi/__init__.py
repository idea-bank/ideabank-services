"""
    :module_name: ideabank_webapi
    :module_summary: An API for the services utilized by the Idea Bank application
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
from typing import Union

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .handlers.creators import AccountCreationHandler
from .handlers.retrievers import AuthenticationHandler
from .services import RegisteredService, AccountsDataService
from .models.artifacts import (
        CredentialSet,
        AuthorizationToken,
        EndpointErrorMessage,
        EndpointInformationalMessage
)

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


@app.post(
        "/accounts/create",
        response_model=Union[EndpointInformationalMessage, EndpointErrorMessage])
def create_account(
        new_account: CredentialSet,
        response: JSONResponse
        ):
    """Create a new account with the given display name and password if available"""
    handler = AccountCreationHandler()
    handler.use_service(RegisteredService.ACCOUNTS_DS, AccountsDataService())
    handler.receive(new_account)
    response.status_code = handler.result.code
    return handler.result.body


@app.post(
        "/accounts/authenticate",
        response_model=Union[EndpointErrorMessage, AuthorizationToken]
        )
def authenticate(
        credentials: CredentialSet,
        response: JSONResponse
        ):
    """
        Verify the provided credentials against stored version.
        Provides the client with an AuthorizationToken if correct
    """
    handler = AuthenticationHandler()
    handler.use_service(RegisteredService.ACCOUNTS_DS, AccountsDataService())
    handler.receive(credentials)
    response.status_code = handler.result.code
    return handler.result.body
