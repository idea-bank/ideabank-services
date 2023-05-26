"""
    :module name: creators
    :module summary: endpoint classes that deal with data creation
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import secrets
import hashlib

from fastapi import status

from . import BaseEndpointHandler

from ..services import RegisteredService
from ..models import CredentialSet, AccountRecord
from ..models import EndpointSuccessResponse, EndpointErrorResponse

LOGGER = logging.getLogger(__name__)


class AccountCreationHandler(BaseEndpointHandler):
    """Endpoint handler dealing with account creation"""

    def _do_data_ops(self, request: CredentialSet):
        LOGGER.info("Securing new account credentials")
        secured_request = self._secure_payload(
                username=request.display_name,
                raw_pass=request.password
                )
        LOGGER.info("Creating new account record")
        with self.get_service(RegisteredService.ACCOUNTS_DS) as service:
            service.add_query(service.create_account(
                    username=secured_request.display_name,
                    hashed_password=secured_request.password_hash,
                    salt_value=secured_request.salt_value
                ))
            service.exec_next()
            return service.results.one().display_name

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

    def _build_success_response(self, body: str):
        LOGGER.info("Account for %s successfully created", body)
        self._result = EndpointSuccessResponse(
                code=status.HTTP_201_CREATED,
                msg=f'Account created for {body}'
                )

    def _build_error_response(self, body: str):
        LOGGER.info("Account for %s could not be created", body)
        self._result = EndpointErrorResponse(
                code=status.HTTP_403_FORBIDDEN,
                err_msg=f'Display name `{body}` is not available'
                )
