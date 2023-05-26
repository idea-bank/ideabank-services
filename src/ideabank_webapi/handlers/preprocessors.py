"""
    :module name: preprocessors
    :module summary: extensions of the base handler that add extra steps to the receive method
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
from typing import Optional

import jwt
from fastapi import status

from . import (
        BaseEndpointHandler,
        EndpointHandlerStatus
    )
from ..config import ServiceConfig
from ..exceptions import NotAuthorizedError
from ..models import (
        AuthorizationToken,
        EndpointErrorResponse,
        AuthorizedPayload
    )

LOGGER = logging.getLogger(__name__)


class AuthorizationRequired(BaseEndpointHandler):
    """Endpoint handler guard that adds an authorization check before proceding"""

    def _check_if_authorized(self, authorization: AuthorizationToken):
        """Verify the given authorization token
        Arguments:
            authorization: [AuthorizationToken] the token to validate
        Returns:
            None if authorization check succeeds
        Raises:
            NotAuthorizedError if authorization check fails
        """
        LOGGER.info("Validating the presented authorization token")
        try:
            claims = jwt.decode(
                authorization.token,
                ServiceConfig.AuthKey.JWT_SIGNER,
                ServiceConfig.AuthKey.JWT_HASHER,
                options={
                    'require': ['username', 'exp', 'nbf']
                    }
                )
            if claims['username'] != authorization.presenter:
                LOGGER.error(
                        "Token presenter (%s) is not the owner (%s)",
                        authorization.presenter,
                        claims['username']
                        )
                raise NotAuthorizedError(
                        "Cannot verify ownership of token."
                        )
        except jwt.exceptions.InvalidTokenError as err:
            LOGGER.error("Presented token is malformed")
            raise NotAuthorizedError(
                    "Invalid token presented."
                    ) from err

    def _build_error_response(self, body: Optional[str]) -> None:
        """Set the result of this handler to be unauthorized
        Arguments:
            msg: [str] optional message to include in the access denied response
        """
        self._result = EndpointErrorResponse(
                code=status.HTTP_401_UNAUTHORIZED,
                msg=body
                )

    def receive(self, incoming_data: AuthorizedPayload) -> None:
        """Handles the incoming data as a request to this handlers endpoint
        Arguments:
            incoming_data: [BasePayload] the payload to pass to this handler
        Returns:
            [None] use result to obtain handler results
        """
        try:
            self._check_if_authorized(incoming_data.auth_token)
            super().receive(incoming_data)
        except NotAuthorizedError as err:
            AuthorizationRequired._build_error_response(self, str(err))
            self._status = EndpointHandlerStatus.ERROR
