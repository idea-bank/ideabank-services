"""Tests for base handler template class"""

from unittest.mock import patch
import pytest
from fastapi import status

from ideabank_webapi.handlers import (
        EndpointResponse,
        EndpointRequest,
        BaseEndpointHandler,
        EndpointHandlerStatus
        )
from ideabank_webapi.services import (
        QueryService,
        S3Crud,
        RegisteredService
        )

from ideabank_webapi.exceptions import (
        IdeaBankDataServiceException,
        IdeaBankEndpointHandlerException,
        HandlerNotIdleException,
        NoRegisteredProviderError,
        ProviderMisconfiguredError
        )


@pytest.fixture
def test_handler():
    class TestHandler(BaseEndpointHandler):

        @property
        def payload_class(self): return EndpointRequest

        @property
        def result_class(self): return EndpointResponse

        def _do_data_ops(self, request):
            return {'number': 1}

        def _build_success_response(self, body):
            return EndpointResponse(
                    code=status.HTTP_200_OK,
                    msg='Data retrieved successfully',
                    body=body
                    )

        def _build_error_response(self, body):
            return EndpointResponse(
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    msg='An error occurred',
                    body=body
                    )
    return TestHandler


def test_cannot_instantiate_base_handler():
    with pytest.raises(TypeError):
        BaseEndpointHandler()


def test_handler_subclass_has_payload_and_result_classes_set(test_handler):
    th = test_handler()
    assert th.payload_class == EndpointRequest
    assert th.result_class == EndpointResponse


def test_handler_state_is_complete_when_successful(test_handler):
    th = test_handler()
    th.receive(th.payload_class(
        method='GET',
        resource='/test/resource'
        ))
    assert th.status == EndpointHandlerStatus.COMPLETE
    assert th.result == EndpointResponse(
            code=status.HTTP_200_OK,
            )


@pytest.mark.parametrize("error_type", [
    IdeaBankEndpointHandlerException,
    IdeaBankDataServiceException
    ])
def test_handler_state_is_error_when_failed(test_handler, error_type):
    th = test_handler()
    with patch.object(
            type(th),
            '_do_data_ops',
            side_effect=error_type
            ) as err:
        th.receive(th.payload_class(
            method='GET',
            resource='/test/resource'
            ))
        assert th.status == EndpointHandlerStatus.ERROR
        assert th.result == th.result_class(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        err.assert_called_once()


def test_handler_can_use_a_specific_service(test_handler):
    th = test_handler()
    th.use_service(RegisteredService.RAW_DB, QueryService())
    assert len(th._services) > 0


def test_non_idle_handler_cannot_receive(test_handler):
    th = test_handler()
    th._status = EndpointHandlerStatus.PROCESSING
    with pytest.raises(HandlerNotIdleException):
        th.receive(th.payload_class(
            method='GET',
            resource='/test/resource'
        ))


def test_use_of_service_provider(test_handler):
    th = test_handler()
    th.use_service(RegisteredService.RAW_DB, QueryService())
    provider = th.get_service(RegisteredService.RAW_DB)
    assert isinstance(provider, QueryService)


@pytest.mark.xfail(raises=NoRegisteredProviderError)
def test_use_of_missing_service_provider(test_handler):
    th = test_handler()
    th.get_service(RegisteredService.RAW_DB)


@pytest.mark.xfail(raises=ProviderMisconfiguredError)
def test_use_of_misconfigured_service_provider(test_handler):
    th = test_handler()
    th.use_service(RegisteredService.RAW_DB, S3Crud())
    th.get_service(RegisteredService.RAW_DB)
