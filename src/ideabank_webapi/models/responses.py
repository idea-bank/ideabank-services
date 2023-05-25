
from typing import Optional

from pydantic import BaseModel


class EndpointResponse(BaseModel):  # pylint:disable=too-few-public-methods
    """Base class for all response model produced by this API"""
    code: int


class EndpointSuccessResponse(EndpointResponse):  # pylint:disable=too-few-public-methods
    """Base class for all successful response models produced by this API"""
    msg: Optional[str]


class EndpointErrorResponse(EndpointResponse):  # pylint:disable=too-few-public-methods
    """Base class for all error response models produced by this API"""
    err_msg: Optional[str]
