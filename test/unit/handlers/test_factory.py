"""Tests for the handler factory"""

import importlib
import inspect
import pytest
import itertools
from ideabank_webapi.services import RegisteredService
from ideabank_webapi.exceptions import NoSuchHandlerException
from ideabank_webapi.handlers import BaseEndpointHandler
from ideabank_webapi.handlers.factory import EndpointHandlerFactory


def setup_module():
    importlib.import_module('ideabank_webapi.handlers.creators')
    importlib.import_module('ideabank_webapi.handlers.retrievers')
    importlib.import_module('ideabank_webapi.handlers.erasers')


def find_handlers(cls):
    return set(cls.__subclasses__()).union(
            [
                s
                for c in cls.__subclasses__()
                for s in find_handlers(c)
                if not inspect.isabstract(s)
                ]
            )


@pytest.mark.parametrize("handler", find_handlers(BaseEndpointHandler))
def test_factory_yields_handler_instance(handler):
    if handler.__name__ == 'AuthorizationRequired':
        with pytest.raises(TypeError):
            factory = EndpointHandlerFactory()
            assert isinstance(factory.create_handler(handler.__name__), handler)
    else:
        factory = EndpointHandlerFactory()
        assert isinstance(factory.create_handler(handler.__name__), handler)


@pytest.mark.xfail(raises=NoSuchHandlerException)
def test_factory_fails_when_given_invalid_handler():
    factory = EndpointHandlerFactory()
    factory.create_handler('NotAHandlerClass')


@pytest.mark.parametrize("services", itertools.chain(
    itertools.permutations(RegisteredService, 1),
    itertools.permutations(RegisteredService, 2)
    )
)
def test_factory_includes_services_with_instance_request(services):
    factory = EndpointHandlerFactory()
    handler = factory.create_handler('AuthenticationHandler', *services)
    for service in services:
        assert isinstance(handler.get_service(service), service.value)
