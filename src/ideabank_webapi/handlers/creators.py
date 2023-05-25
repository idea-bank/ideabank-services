"""
    :module name: creators
    :module summary: endpoint classes that deal with data creation (POST)
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import secrets
import hashlib

from pydantic import BaseModel  # pylint:disable=no-name-in-module
from fastapi import status

from . import (
        BaseEndpointHandler,
        EndpointResponse,
        EndpointRequest
        )

from ..services import RegisteredService
from ..models.artifacts import CredentialSet

LOGGER = logging.getLogger(__name__)


class AccountCreationRequest(EndpointRequest):  # pylint:disable=too-few-public-methods
    """Request modeling the data required to create and idea bank account"""
    new_account: CredentialSet


class AccountCreationResponse(EndpointResponse):  # pylint:disable=too-few-public-methods
    """Response modeling the data sent when account creation is invoked"""
    msg: str


class AccountCreationHandler(BaseEndpointHandler):
    """Endpoint handler dealing with account creation"""

    class AccountRecord(BaseModel):  # pylint:disable=too-few-public-methods
        display_name: str
        password_hash: str
        salt_value: str

    @property
    def payload_class(self):
        """Class used to parse and validate payload"""
        return AccountCreationRequest

    @property
    def result_class(self):
        """Class used to parse and validate payload"""
        return AccountCreationResponse

    def _do_data_ops(self, request: AccountCreationRequest):
        secured_request = self._secure_payload(
                username=request.new_account.display_name,
                raw_pass=request.new_account.password
                )
        with self.get_service(RegisteredService.ACCOUNTS_DS) as ds:
            ds.add_query(ds.create_account(
                    username=secured_request.display_name,
                    hashed_password=secured_request.password_hash,
                    salt_value=secured_request.salt_value
                ))
            ds.exec_next()
            return ds.results.one()

    def _secure_payload(self, username, raw_pass):
        salt = secrets.token_hex()
        password_hash = hashlib.sha256(
                f'{raw_pass}{salt}'.encode('utf-8')
                ).hexdigest()
        return AccountCreationHandler.AccountRecord(
                display_name=username,
                password_hash=password_hash,
                salt_value=salt
                )

    def _build_success_response(self, body: str):
        self._result = self.result_class(
                code=status.HTTP_201_CREATED,
                msg=f'Account created for {body}'
                )

    def _build_error_response(self, body: str):
        self._result = self.result_class(
                code=status.HTTP_403_FORBIDDEN,
                msg=f'Display name `{body}` is not available'
                )
