"""
    :module name: handlers
    :module summary: collection of classes that respond to api endpoints
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
from typing import Any, Union, Sequence
from abc import ABC, abstractmethod
from enum import Enum

from fastapi import status

from ..models import (
        EndpointResponse,
        EndpointErrorResponse,
        IdeaBankArtifact,
        EndpointPayload
        )
from ..services import RegisteredService
from ..exceptions import (
        BaseIdeaBankAPIException,
        IdeaBankEndpointHandlerException,
        IdeaBankDataServiceException,
        HandlerNotIdleException,
        NoRegisteredProviderError,
        ProviderMisconfiguredError,
        PrematureResultRetrievalException
        )

LOGGER = logging.getLogger(__name__)


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
        LOGGER.debug("Handler status report: %s", str(self._status))
        return self._status

    @property
    def result(self) -> EndpointResponse:
        """Returns the results of this handler. May be None if not completed
        Returns:
            EndpointResponse
        Raises:
            PrematureResultRetrievalException if handler is not complete/error
        """
        if self.status not in [EndpointHandlerStatus.COMPLETE, EndpointHandlerStatus.ERROR]:
            LOGGER.error("Handler is not finished. Result is unavailable")
            raise PrematureResultRetrievalException(
                    "Attempted to read handler results before they were ready"
                    )
        return self._result

    def use_service(self, name: RegisteredService, provider: Any) -> None:
        """Register a service provider that this handler can use.
        The current provider is replaced if the named service already exist
        Arguments:
            name: [RegisteredService] enum member of known services
            provider: instance of [name] that provides the service
        """
        LOGGER.debug("Using service provider for %s", str(name))
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
                LOGGER.error(
                        "Expected %s instance, got %s instance",
                        name.value.__name__,
                        provider.__class__.__name__
                        )
                raise ProviderMisconfiguredError(
                        f"Expected instance of {name.value.__name__}, "
                        f"got instance of {provider.__class__.__name__}"
                        )
            LOGGER.debug("Retrieved registered service provider: %s", str(name))
            return provider
        except KeyError as err:
            LOGGER.error("No service registered under %s", str(name))
            raise NoRegisteredProviderError(
                    f"No service registered under {name}"
                    ) from err

    def receive(self, incoming_data: Union[IdeaBankArtifact, EndpointPayload]) -> None:
        """Handles the incoming data as a request to this handlers endpoint
        Arguments:
            incoming_data: [BasePayload] the payload to pass to this handler
        Returns:
            [None] use results() to obtain handler results
        """
        if self.status != EndpointHandlerStatus.IDLE:
            LOGGER.error("Handler not ready to receive")
            raise HandlerNotIdleException(
                    f"Expected handler to be idle, but was {self.status}"
                    )
        self._status = EndpointHandlerStatus.PROCESSING
        try:
            LOGGER.info("Attemping normal workflow %s", self.__class__.__name__)
            data = self._do_data_ops(incoming_data)
            self._build_success_response(data)
            self._status = EndpointHandlerStatus.COMPLETE
            LOGGER.info("Completed normal workflow successfully")
        except IdeaBankEndpointHandlerException as err:
            LOGGER.exception(err)
            LOGGER.error("Normal flow unsuccessful, starting error workflow")
            self._build_error_response(str(err))
            self._status = EndpointHandlerStatus.ERROR
        except IdeaBankDataServiceException as err:
            LOGGER.exception(err)
            LOGGER.error("Normal flow unsuccessful, starting error workflow")
            self._build_error_response(str(err))
            self._status = EndpointHandlerStatus.ERROR

    @abstractmethod
    def _do_data_ops(
            self,
            request: Any
            ) -> Union[IdeaBankArtifact, Sequence[IdeaBankArtifact], str]:
        """Complete the data requested operation in the payload from handler services
        Arguments:
            [BasePayload] data request
        Returns:
            Union[IdeaBankArtifact, Sequence[IdeaBankArtifact], str]
        Raises:
            [BaseIdeaBankDataServiceException] for any service related issues
        """

    @abstractmethod
    def _build_success_response(
            self,
            success_code: int,
            requested_data: Union[IdeaBankArtifact, Sequence[IdeaBankArtifact], str]
            ):
        """Create the response body as a result of a successful handler return
        Arguments:
            success_code: [int] the HTTP status code to use in the response
            requested_data:
                Union[IdeaBankArtifact, Sequence[IdeaBankArtifact], str]
                The data to include in the body of the response
        Returns:
            None
        """

    @abstractmethod
    def _build_error_response(
            self,
            exc: BaseIdeaBankAPIException
            ):
        """Create a response body as a result of a failed handler return
        Arguments:
            exc: [BaseIdeaBankAPIException] exception causing the issue
        Returns:
            None
        """
        self._result = EndpointErrorResponse(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                err_msg=(str(exc))
                )
