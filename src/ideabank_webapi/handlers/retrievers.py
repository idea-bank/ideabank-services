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
from ..models import CredentialSet, AccountRecord, AuthorizationToken, ProfileView
from ..models import EndpointErrorMessage, EndpointResponse
from ..exceptions import (
        InvalidCredentialsException,
        BaseIdeaBankAPIException,
        RequestedDataNotFound
    )

LOGGER = logging.getLogger(__name__)


class AuthenticationHandler(BaseEndpointHandler):
    """Endpoint handler dealing into account authenticaiton"""

    def _do_data_ops(self, request: CredentialSet) -> str:
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


class ProfileRetrievalHandler(BaseEndpointHandler):
    """Endpoint handler dealing with profile retrievals"""

    def _do_data_ops(self, request: str) -> ProfileView:
        try:
            LOGGER.info("Looking up profile information: %s", request)
            with self.get_service(RegisteredService.ACCOUNTS_DS) as service:
                service.add_query(service.fetch_account_profile(
                    display_name=request
                    ))
                service.exec_next()
                result = service.results.one()
                return ProfileView(
                    preferred_name=result.preferred_name,
                    biography=result.biography,
                    avatar_url=service.share_item(f'avatars/{request}')
                        )
        except NoResultFound as err:
            LOGGER.error("No account record found: %s", request)
            raise RequestedDataNotFound(
                    f'Profile for {request} is not available'
                    ) from err

    def _build_success_response(self, requested_data: ProfileView):
        self._result = EndpointResponse(
                code=status.HTTP_200_OK,
                body=requested_data
                )

    def _build_error_response(self, exc: BaseIdeaBankAPIException):
        if isinstance(exc, RequestedDataNotFound):
            self._result = EndpointResponse(
                    code=status.HTTP_404_NOT_FOUND,
                    body=EndpointErrorMessage(
                        err_msg=str(exc)
                        )
                    )
        else:
            super()._build_error_response(exc)
