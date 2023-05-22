"""
    :module name: handlers
    :module summary: collection of classes that respond to api endpoints
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

from typing import Any, Optional, Dict, List, Union
from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel  # pylint:disable=no-name-in-module

from ..services import RegisteredService
from ..exceptions import (
        IdeaBankEndpointHandlerException,
        IdeaBankDataServiceException,
        HandlerNotIdleException
        )


class BaseResult(BaseModel):  # pylint:disable=too-few-public-methods
    """Base structure of a reponse form an endpoint handler"""
    code: int
    msg: Optional[str]
    body: Any


class BasePayload(BaseModel):  # pylint:disable=too-few-public-methods
    """Base structure of a payload expected by an endpoint handler"""
    path_variables: Dict[str, Any]
    query_parameters: Dict[str, Any]
    body: Dict[str, Union[Dict[str, Any], List[Any], Any]]


class EndpointHandlerStatus(Enum):
    """Enumeration of handler states"""
    IDLE = 0  # Created, but .receive() method has not yet ben called
    PROCESSING = 1  # call to .receive() made, but has not yet finished
    COMPLETE = 2  # call to .receive() completed without errors
    ERROR = 3  # call to .receive() complete with error(s)


class BaseEndpointHandler(ABC):
    """Base template handler for API endpoints.
    Ideally, each endpoint has its own specialized handler class
    Attributes:
        PAYLOAD_CLASS: the class modeling the structure of the payload if any
        RESULT_CLASS: the class modeling the structure of the response
        status: the state of the handler. One of (idle, processing, complete, error)
        result: the data to be included in the response body
    """

    def __init__(self):
        self._status = EndpointHandlerStatus.IDLE
        self._result = None
        self._services = {}

    @property
    def status(self) -> EndpointHandlerStatus:
        """Return the status of this handler
        Returns:
            EndpointHandlerStatus enum member
        """
        return self._status

    @property
    def result(self) -> Optional[BaseResult]:
        """Returns the results of this handler. May be None if not completed
        Returns:
            [Optional[BaseResult]]
        """
        return self._result

    def use_service(self, name: RegisteredService, provider: Any) -> None:
        """Register a service provider that this handler can use.
        The current provider is replaced if the named service already exist
        Arguments:
            name: [RegisteredService] enum member of known services
            provider: instance of [name] that provides the service
        """
        self._services.update({name: provider})

    @property
    @abstractmethod
    def payload_class(self):
        """Class that models the payload of this handler"""

    @property
    @abstractmethod
    def result_class(self):
        """Class that models the results of this handler"""

    def receive(self, incoming_data: BasePayload) -> None:
        """Handles the incoming data as a request to this handlers endpoint
        Arguments:
            incoming_data: [BasePayload] the payload to pass to this handler
        Returns:
            [None] use results() to obtain handler results
        """
        if self.status != EndpointHandlerStatus.IDLE:
            raise HandlerNotIdleException(
                    f"Expected handler to be idle, but was {self.status}"
                    )
        self._services = EndpointHandlerStatus.PROCESSING
        try:
            data = self._fetch_requested_data(incoming_data)
            self._result = self._build_success_response(data)
            self._status = EndpointHandlerStatus.COMPLETE
        except IdeaBankEndpointHandlerException as err:
            self._result = self._build_error_response(str(err))
            self._status = EndpointHandlerStatus.ERROR
        except IdeaBankDataServiceException as err:
            self._result = self._build_error_response(str(err))
            self._status = EndpointHandlerStatus.ERROR

    @abstractmethod
    def _fetch_requested_data(self, request: BasePayload) -> dict:
        """Fetch the data requested in the payload from handler services
        Arguments:
            [BasePayload] data request
        Returns:
            [dict] mapping of requested data
        Raises:
            [BaseIdeaBankDataServiceException] for any service related issues
        """

    @abstractmethod
    def _build_success_response(self, body: Any):
        """Create the response body as a result of a successful handler return
        Arguments:
            [dict] data that might be included in the body
        Returns:
            None
        """

    @abstractmethod
    def _build_error_response(self, body: Any):
        """Create a response body as a result of a failed handler return
        Arguments:
            [dict] data that might be included in the body
        Returns:
            None
        """
