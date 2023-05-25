"""
    :module name: payloads
    :module summary: classes the model the payloads accepted by endpoint handlers
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

from pydantic import BaseModel  # pylint:disable=no-name-in-module

from .artifacts import AuthorizationToken


class EndpointPayload(BaseModel):  # pylint:disable=too-few-public-methods
    """Base payload model for data passed to endpoint handlers"""


class AuthorizedPayload(EndpointPayload):  # pylint:disable=too-few-public-methods
    """Models a payload that includes an authorization token"""
    auth_token: AuthorizationToken
