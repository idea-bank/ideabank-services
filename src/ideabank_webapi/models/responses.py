"""
    :module name: responses
    :module summary: classes that model the responses delivered by this API
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

from typing import Optional

from pydantic import BaseModel  # pylint:disable=no-name-in-module


class EndpointResponse(BaseModel):  # pylint:disable=too-few-public-methods
    """Base class for all response model produced by this API"""
    code: int


class EndpointSuccessResponse(EndpointResponse):  # pylint:disable=too-few-public-methods
    """Base class for all successful response models produced by this API"""
    msg: Optional[str]


class EndpointErrorResponse(EndpointResponse):  # pylint:disable=too-few-public-methods
    """Base class for all error response models produced by this API"""
    err_msg: Optional[str]
