"""Tests for base handler template class"""

from unittest.mock import patch
import pytest
from fastapi import status

from ideabank_webapi.handlers import (
        BaseResult,
        BasePayload,
        BaseEndpointHandler,
        EndpointHandlerStatus
        )
from ideabank_webapi.services import (
        QueryService,
        RegisteredService
        )

from ideabank_webapi.exceptions import (
        IdeaBankDataServiceException,
        IdeaBankEndpointHandlerException,
        HandlerNotIdleException
        )


@pytest.fixture
def test_handler():
    class TestHandler(BaseEndpointHandler):

        @property
        def payload_class(self): return BasePayload

        @property
        def result_class(self): return BaseResult

        def _do_data_ops(self, request):
            return {'number': 1}

        def _build_success_response(self, body):
            return BaseResult(
                    code=status.HTTP_200_OK,
                    msg='Data retrieved successfully',
                    body=body
                    )

        def _build_error_response(self, body):
            return BaseResult(
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
    assert th.payload_class == BasePayload
    assert th.result_class == BaseResult


def test_handler_state_is_complete_when_successful(test_handler):
    th = test_handler()
    th.receive(th.payload_class(
        path_variables={},
        query_parameters={},
        body={}
        ))
    assert th.status == EndpointHandlerStatus.COMPLETE
    assert th.result == BaseResult(
            code=status.HTTP_200_OK,
            msg='Data retrieved successfully',
            body={'number': 1}
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
            path_variables={},
            query_parameters={},
            body={}
            ))
        assert th.status == EndpointHandlerStatus.ERROR
        assert th.result == th.result_class(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                msg='An error occurred',
                body=''
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
            path_variables={},
            query_parameters={},
            body={}
        ))
