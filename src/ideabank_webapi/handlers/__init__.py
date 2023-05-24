"""
    :module name: handlers
    :module summary: collection of classes that respond to api endpoints
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

from typing import Any, Optional
from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel  # pylint:disable=no-name-in-module

from ..services import RegisteredService
from ..exceptions import (
        IdeaBankEndpointHandlerException,
        IdeaBankDataServiceException,
        HandlerNotIdleException,
        NoRegisteredProviderError,
        ProviderMisconfiguredError
        )


class EndpointResponse(BaseModel):  # pylint:disable=too-few-public-methods
    """Base structure of a reponse form an endpoint handler"""
    code: int


class EndpointRequest(BaseModel):  # pylint:disable=too-few-public-methods
    """Base structure of a payload expected by an endpoint handler"""
    method: str
    resource: str


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
    def result(self) -> Optional[EndpointResponse]:
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

    def get_service(self, name: RegisteredService) -> Any:
        """Obtain the service provider instance registed under name
        Arguments:
            name: [RegisteredService] enum member of knwon services
        Returns:
            API service provider
        Raises:
            NoRegisteredProviderError: when no provider is registered under name
            ProviderMisconfiguredError: when the expected provider is incorrect
        """
        try:
            provider = self._services[name]
            if not isinstance(provider, name.value):
                raise ProviderMisconfiguredError(
                        f"Expected instance of {name.value.__name__}, "
                        f"got instance of {provider.__class__.__name__}"
                        )
            return provider
        except KeyError as err:
            raise NoRegisteredProviderError(
                    f"No service registered under {name}"
                    ) from err

    @property
    @abstractmethod
    def payload_class(self):
        """Class that models the payload of this handler"""

    @property
    @abstractmethod
    def result_class(self):
        """Class that models the results of this handler"""

    def receive(self, incoming_data: EndpointRequest) -> None:
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
        self._status = EndpointHandlerStatus.PROCESSING
        try:
            data = self._do_data_ops(incoming_data)
            self._result = self._build_success_response(data)
            self._status = EndpointHandlerStatus.COMPLETE
        except IdeaBankEndpointHandlerException as err:
            self._result = self._build_error_response(str(err))
            self._status = EndpointHandlerStatus.ERROR
        except IdeaBankDataServiceException as err:
            self._result = self._build_error_response(str(err))
            self._status = EndpointHandlerStatus.ERROR

    @abstractmethod
    def _do_data_ops(self, request: EndpointRequest) -> EndpointResponse:
        """Complete the data requested operation in the payload from handler services
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
