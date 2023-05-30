"""
    :module_name: ideabank_webapi
    :module_summary: An API for the services utilized by the Idea Bank application
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
from typing import Union

from fastapi import FastAPI, status, Header
from fastapi.responses import JSONResponse

from .handlers.creators import (
        AccountCreationHandler,
        ConceptCreationHandler,
        ConceptLinkingHandler
        )
from .handlers.retrievers import AuthenticationHandler, ProfileRetrievalHandler
from .services import RegisteredService, AccountsDataService, ConceptsDataService
from .models.artifacts import (
        CredentialSet,
        AuthorizationToken,
        ProfileView,
        ConceptSimpleView,
        ConceptLinkRecord,
        EstablishLink,
        EndpointErrorMessage,
        EndpointInformationalMessage
)
from .models.payloads import ConceptDataPayload, CreateConcept

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
        status_code=status.HTTP_201_CREATED,
        responses={
            status.HTTP_201_CREATED: {
                'model': EndpointInformationalMessage
                },
            status.HTTP_403_FORBIDDEN: {
                'model': EndpointErrorMessage
                }
            }
        )
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
        responses={
            status.HTTP_200_OK: {
                'model': AuthorizationToken
                },
            status.HTTP_401_UNAUTHORIZED: {
                'model': EndpointErrorMessage
                }
            }
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


@app.get(
        "/accounts/{display_name}/profile",
        responses={
            status.HTTP_200_OK: {
                'model': ProfileView
                },
            status.HTTP_404_NOT_FOUND: {
                'model': EndpointErrorMessage
                }
            }
        )
def fetch_profile(
        display_name: str,
        response: JSONResponse
        ):
    """Fetches the profile view of the request display name if it exists"""
    handler = ProfileRetrievalHandler()
    handler.use_service(RegisteredService.ACCOUNTS_DS, AccountsDataService())
    handler.receive(display_name)
    response.status_code = handler.result.code
    return handler.result.body


@app.post(
        "/concepts",
        status_code=status.HTTP_201_CREATED,
        responses={
            status.HTTP_201_CREATED: {
                'model': ConceptSimpleView
                },
            status.HTTP_403_FORBIDDEN: {
                'model': EndpointErrorMessage
                },
            status.HTTP_401_UNAUTHORIZED: {
                'model': EndpointErrorMessage
                }
            }
        )
def create_concept(
        concept_data: ConceptDataPayload,
        response: JSONResponse,
        authorization: str = Header(default="")
        ):
    """Creates a new concept with the given data if valid/available AND authroization is OK"""
    handler = ConceptCreationHandler()
    handler.use_service(RegisteredService.CONCEPTS_DS, ConceptsDataService())
    handler.receive(
            CreateConcept(
                auth_token=AuthorizationToken(
                    token=authorization,
                    presenter=concept_data.author
                    ),
                **concept_data.dict()
                )
            )
    response.status_code = handler.result.code
    return handler.result.body


@app.post(
        "/links",
        status_code=status.HTTP_201_CREATED,
        responses={
            status.HTTP_201_CREATED: {
                'model': ConceptLinkRecord
                },
            status.HTTP_403_FORBIDDEN: {
                'model': EndpointErrorMessage
                },
            status.HTTP_401_UNAUTHORIZED: {
                'model': EndpointErrorMessage
                }
            }
        )
def create_link(
        link_data: ConceptLinkRecord,
        response: JSONResponse,
        authorization: str = Header(default="")
        ):
    """Creates a link between two concepts in valid and authorization is OK"""
    handler = ConceptLinkingHandler()
    handler.use_service(RegisteredService.CONCEPTS_DS, ConceptsDataService())
    handler.receive(
            EstablishLink(
                auth_token=AuthorizationToken(
                    token=authorization,
                    presenter=link_data.descendant.split('/')[0]
                    ),
                **link_data.dict()
                )
            )
    response.status_code = handler.result.code
    return handler.result.body
