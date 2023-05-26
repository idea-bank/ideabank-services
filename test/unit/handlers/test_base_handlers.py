"""Tests for base handler template class"""

import json
from unittest.mock import patch
import pytest
from fastapi import status

from ideabank_webapi.handlers import (
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
        ProviderMisconfiguredError,
        PrematureResultRetrievalException
        )
from ideabank_webapi.models import EndpointResponse, EndpointPayload, EndpointErrorResponse


class RecoverableServiceException(IdeaBankDataServiceException):
    pass


class UnrecoverableServiceException(IdeaBankEndpointHandlerException):
    pass


@pytest.fixture
def test_handler():
    class TestHandler(BaseEndpointHandler):

        def _do_data_ops(self, request):
            return {'number': 1}

        def _build_success_response(self, requested_data):
            self._result = EndpointResponse(
                    code=status.HTTP_200_OK,
                    msg=json.dumps(requested_data)
                    )

        def _build_error_response(self, exc):
            print(type(exc), isinstance(exc, RecoverableServiceException))
            if isinstance(exc, RecoverableServiceException):
                self._result = EndpointErrorResponse(
                        code=status.HTTP_400_BAD_REQUEST,
                        err_msg=''
                        )
            else:
                super()._build_error_response(exc)

    return TestHandler


@pytest.mark.xfail(raises=TypeError)
def test_cannot_instantiate_base_handler():
    BaseEndpointHandler()


def test_handler_state_is_complete_when_successful(test_handler):
    th = test_handler()
    th.receive(EndpointPayload())
    assert th.status == EndpointHandlerStatus.COMPLETE
    assert th.result == EndpointResponse(
            code=status.HTTP_200_OK,
            msg=json.dumps(th._do_data_ops(EndpointPayload()))
            )


@pytest.mark.parametrize("error_type, error_code", [
    (RecoverableServiceException, status.HTTP_400_BAD_REQUEST),
    (UnrecoverableServiceException, status.HTTP_500_INTERNAL_SERVER_ERROR)
    ])
def test_handler_state_is_error_when_failed(test_handler, error_type, error_code):
    th = test_handler()
    with patch.object(
            type(th),
            '_do_data_ops',
            side_effect=error_type
            ) as err:
        th.receive(EndpointPayload())
        assert th.status == EndpointHandlerStatus.ERROR
        assert th.result == EndpointErrorResponse(
                code=error_code,
                err_msg=''
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
        th.receive(EndpointPayload())


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


@pytest.mark.xfail(raises=PrematureResultRetrievalException)
def test_getting_results_before_ready_throws_error(test_handler):
    th = test_handler()
    th.result
