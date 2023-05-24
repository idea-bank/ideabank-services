"""
    :module name: guards
    :module summary: extensions of the base endpoint handler that add extra steps to the receive method
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
    auth_token: AuthorizationToken


class AccessDenied(EndpointResponse):  # pyling:disable=too-few-public-methods
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
                        "Cannnot verify ownership of token."
                        )
        except jwt.exceptions.InvalidTokenError:
            raise NotAuthorizedError(
                    "Invalid token presented."
                    )

    def _deny_access(self, msg: Optional[str]) -> None:
        """Set the result of this handler to be unauthorized
        Arguments:
            msg: [str] optional message to include in the access denied response
        """
        self._results = AccessDenied(
                code=status.HTTP_401_UNAUTHORIZED,
                msg=msg if msg else None,
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
            BaseEndpointHandler.receive(incoming_data)
        except NotAuthorizedError as err:
            self._deny_access(str(err))
            self._status = EndpointHandlerStatus.ERROR
