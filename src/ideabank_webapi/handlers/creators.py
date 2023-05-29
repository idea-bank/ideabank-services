"""
    :module name: creators
    :module summary: endpoint classes that deal with data creation
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import secrets
import hashlib

from fastapi import status
from sqlalchemy.exc import IntegrityError

from . import BaseEndpointHandler
from .preprocessors import AuthorizationRequired
from ..services import RegisteredService
from ..models import (
        CredentialSet,
        AccountRecord,
        EndpointErrorMessage,
        EndpointInformationalMessage,
        EndpointResponse,
        CreateConcept,
        ConceptSimpleView
        )
from ..exceptions import DuplicateRecordException, BaseIdeaBankAPIException

LOGGER = logging.getLogger(__name__)


class AccountCreationHandler(BaseEndpointHandler):
    """Endpoint handler dealing with account creation"""

    def _do_data_ops(self, request: CredentialSet):
        LOGGER.info("Securing new account credentials")
        secured_request = self._secure_payload(
                username=request.display_name,
                raw_pass=request.password
                )
        try:
            LOGGER.info("Creating new account record")
            with self.get_service(RegisteredService.ACCOUNTS_DS) as service:
                service.add_query(service.create_account(
                        username=secured_request.display_name,
                        hashed_password=secured_request.password_hash,
                        salt_value=secured_request.salt_value
                    ))
                service.exec_next()
                return service.results.one().display_name
        except IntegrityError as err:
            LOGGER.error(
                    "Attempted to add duplicate record: %s",
                    request.display_name
                    )
            raise DuplicateRecordException(
                    f"{request.display_name}"
                    ) from err

    def _secure_payload(self, username, raw_pass):
        salt = secrets.token_hex()
        password_hash = hashlib.sha256(
                f'{raw_pass}{salt}'.encode('utf-8')
                ).hexdigest()
        return AccountRecord(
                display_name=username,
                password_hash=password_hash,
                salt_value=salt
                )

    def _build_success_response(self, requested_data: str):
        LOGGER.info("Account for %s successfully created", requested_data)
        self._result = EndpointResponse(
                code=status.HTTP_201_CREATED,
                body=EndpointInformationalMessage(
                    msg=f'Account for {requested_data} successfully created'
                    )
                )

    def _build_error_response(self, exc: BaseIdeaBankAPIException):
        LOGGER.info("Account could not be created")
        if isinstance(exc, DuplicateRecordException):
            self._result = EndpointResponse(
                    code=status.HTTP_403_FORBIDDEN,
                    body=EndpointErrorMessage(
                        err_msg=f'Account not created: {str(exc)} not available'
                        )
                    )
        else:
            super()._build_error_response(exc)


class ConceptCreationHandler(AuthorizationRequired):
    """Endpoint handler dealing with concept creation"""

    def _do_data_ops(self, request: CreateConcept):
        LOGGER.info(
                "Creating concept record `%s` authored by `%s`",
                request.title,
                request.author
                )
        try:
            with self.get_service(RegisteredService.CONCEPTS_DS) as service:
                service.add_query(service.create_concept(
                        author=request.author,
                        title=request.title,
                        description=request.description,
                        diagram=request.diagram
                    ))
                service.exec_next()
                return ConceptSimpleView(
                        identifier=service.results.one().identifier,
                        thumbnail_url=service.share_item(
                            f'thumbanils/{request.author}/{request.title}'
                            )
                        )
        except IntegrityError as err:
            LOGGER.error(
                    "Cannot create duplicate concept `%s/%s`",
                    request.author,
                    request.title
                    )
            raise DuplicateRecordException(
                    f'{request.author}/{request.title}'
                    ) from err

    def _build_success_response(self, requested_data: ConceptSimpleView):
        LOGGER.info("Successfully created the concept `%s`", requested_data.identifier)
        self._result = EndpointResponse(
                code=status.HTTP_201_CREATED,
                body=requested_data
                )

    def _build_error_response(self, exc: BaseIdeaBankAPIException):
        LOGGER.error("Could not create the concept `%s`", str(exc))
        if isinstance(exc, DuplicateRecordException):
            self._result = EndpointResponse(
                    code=status.HTTP_403_FORBIDDEN,
                    body=EndpointErrorMessage(
                        err_msg=f'{str(exc)} is not available'
                        )
                    )
        else:
            super()._build_error_response(exc)
