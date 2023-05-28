"""
    :module name: retrievers
    :module summary: endpoint classes that deal with data retrieval
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import hashlib
import secrets
import datetime

from sqlalchemy.exc import NoResultFound
from fastapi import status
import jwt

from . import BaseEndpointHandler
from ..config import ServiceConfig
from ..services import RegisteredService
from ..models import CredentialSet, AccountRecord, AuthorizationToken
from ..models import EndpointErrorMessage, EndpointResponse
from ..exceptions import InvalidCredentialsException, BaseIdeaBankAPIException

LOGGER = logging.getLogger(__name__)


class AuthenticationHandler(BaseEndpointHandler):
    """Endpoint handler dealing into account authenticaiton"""

    def _do_data_ops(self, request: CredentialSet):
        try:
            LOGGER.info(
                    "Looking up account information: %s",
                    request.display_name
                    )
            with self.get_service(RegisteredService.ACCOUNTS_DS) as service:
                service.add_query(service.fetch_authentication_information(
                        display_name=request.display_name,
                    ))
                service.exec_next()
                result = service.results.one()
                self.__verify_credentials(request, result)
                return result.display_name
        except NoResultFound as err:
            LOGGER.error(
                    "No account record found: %s",
                    request.display_name
                    )
            raise InvalidCredentialsException(
                    "Invalid display name or password"
                    ) from err

    def _build_success_response(self, requested_data: str):
        self._result = EndpointResponse(
                code=status.HTTP_200_OK,
                body=AuthorizationToken(
                    token=self.__generate_token(requested_data),
                    presenter=requested_data
                    )
                )

    def _build_error_response(self, exc: BaseIdeaBankAPIException):
        if isinstance(exc, InvalidCredentialsException):
            self._result = EndpointResponse(
                    code=status.HTTP_401_UNAUTHORIZED,
                    body=EndpointErrorMessage(
                        err_msg=str(exc)
                        )
                    )
        else:
            super()._build_error_response(exc)

    def __verify_credentials(
            self,
            provided: CredentialSet,
            oracle: AccountRecord
            ):
        LOGGER.info("Comparing provided credentials to stored")
        provided_hash = hashlib.sha256(
                f'{provided.password}{oracle.salt_value}'.encode('utf-8')
                ).hexdigest()
        if secrets.compare_digest(provided_hash, oracle.password_hash):
            LOGGER.debug("Provided credentials match")
            return
        LOGGER.debug("Provided credentials did not match records")
        raise InvalidCredentialsException("Invalid display name or password")

    def __generate_token(self, owner: str) -> str:
        claims = {
                'username': owner,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
                'nbf': datetime.datetime.utcnow() + datetime.timedelta(seconds=2)
                }
        return jwt.encode(
                claims,
                ServiceConfig.AuthKey.JWT_SIGNER,
                ServiceConfig.AuthKey.JWT_HASHER
                )
