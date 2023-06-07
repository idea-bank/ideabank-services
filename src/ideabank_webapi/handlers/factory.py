"""
    :module name: factory
    :module summary: a factory for all known handlers
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import typing
import importlib

from . import BaseEndpointHandler
from ..exceptions import NoSuchHandlerException
from ..services import RegisteredService


LOGGER = logging.getLogger(__name__)
Handler = typing.TypeVar('Handler', bound=BaseEndpointHandler)


class EndpointHandlerFactory:
    """Factory class responsible for constucting endpoint handlers"""

    def __init__(self):
        importlib.import_module('.creators', 'ideabank_webapi.handlers')
        importlib.import_module('.retrievers', 'ideabank_webapi.handlers')
        importlib.import_module('.erasers', 'ideabank_webapi.handlers')
        self._known_handlers = self._discover_concrete_subclasses(BaseEndpointHandler)

    def create_handler(
            self,
            handler_name: str,
            *services: typing.Tuple[RegisteredService]
            ) -> BaseEndpointHandler:
        """Constructs a handler with the given name if it exists and supplies the listed services
        Arguments:
            handler_name: [str] the string name of the service to instantiate
            *services: [Tuple[RegisteredService]] services this handler will use
        Returns:
            [BaseEndpointHander] an implementor of this interface
        Raises:
            NoSuchHandlerException: if handler_name does not correspond to a valid handler name
        """
        handler_class = self._check_for_name(handler_name)
        handler_instance = handler_class()
        for service in services:
            handler_instance.use_service(service)
        return handler_instance

    def _discover_concrete_subclasses(self, cls) -> typing.Set[Handler]:
        """Discover all classes that implement the BaseEndpointHander interface
        Arguments:
            cls: [type] a type to discover the subclasses of
        Returns:
            [Set[Handler]] a set of implementing classes
        """
        LOGGER.debug("Looking for subclasses of %s", str(cls))
        return set(cls.__subclasses__()).union(
                [
                    s
                    for c in cls.__subclasses__()
                    for s in self._discover_concrete_subclasses(c)
                    ]
                )

    def _check_for_name(self, name: str) -> Handler:
        """Checks for the given classname and returns a reference to its constructor
        Arguments:
            name: [str] name of the class to search for
        Returns:
            Reference to a class constructor
        Raises:
            NoSuchHandlerException if no classname match is found
        """
        for c in self._known_handlers:
            if c.__name__ == name:
                LOGGER.info("Found matching handler by name: %s", name)
                return c
        LOGGER.error("No matching handler by name: %s", name)
        raise NoSuchHandlerException(f"Unknown handler name: {name}")
