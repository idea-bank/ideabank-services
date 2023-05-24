"""
    :module name: preprocessors
    :module summary: extensions of the base handler that add extra steps to the receive method
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

from typing import Optional

import jwt
from fastapi import status

from . import (
        BaseEndpointHandler,
        EndpointRequest,
        EndpointResponse,
        EndpointHandlerStatus
    )
from ..config import ServiceConfig
from ..exceptions import NotAuthorizedError
from ..models.artifacts import AuthorizationToken


class AuthorizedRequest(EndpointRequest):  # pylint:disable=too-few-public-methods
    """Models a request that includes an authorization token"""
    auth_token: AuthorizationToken


class AccessDenied(EndpointResponse):  # pylint:disable=too-few-public-methods
    """Models an access denied response with an optional explanation"""
    msg: Optional[str]


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
                raise NotAuthorizedError(
                        "Cannot verify ownership of token."
                        )
        except jwt.exceptions.InvalidTokenError as err:
            raise NotAuthorizedError(
                    "Invalid token presented."
                    ) from err

    def _build_error_response(self, body: Optional[str]) -> None:
        """Set the result of this handler to be unauthorized
        Arguments:
            msg: [str] optional message to include in the access denied response
        """
        self._result = AccessDenied(
                code=status.HTTP_401_UNAUTHORIZED,
                msg=body
                )

    def receive(self, incoming_data: AuthorizedRequest) -> None:
        """Handles the incoming data as a request to this handlers endpoint
        Arguments:
            incoming_data: [BasePayload] the payload to pass to this handler
        Returns:
            [None] use results() to obtain handler results
        """
        try:
            self._check_if_authorized(incoming_data.auth_token)
            super().receive(incoming_data)
        except NotAuthorizedError as err:
            self._build_error_response(str(err))
            self._status = EndpointHandlerStatus.ERROR
