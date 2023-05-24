"""Tests for guard endpoints classes"""

from ideabank_webapi.handlers import (
        EndpointRequest,
        EndpointResponse,
        EndpointHandlerStatus
        )

from ideabank_webapi.handlers.preprocessors import (
        AuthorizationRequired,
        AccessDenied,
        AuthorizedRequest
    )
from ideabank_webapi.models.artifacts import AuthorizationToken
from ideabank_webapi.exceptions import IdeaBankEndpointHandlerException


import pytest
from fastapi import status
import jwt
from unittest.mock import patch


@pytest.fixture
def test_auth_handler():
    class TestAuthorizedHandler(AuthorizationRequired):

        @property
        def payload_class(self): return EndpointRequest

        @property
        def result_class(self): return EndpointResponse

        def _do_data_ops(self, request):
            return {'number': 1}

        def _build_success_response(self, body):
            self._result = EndpointResponse(
                    code=status.HTTP_200_OK
                    )

        def _build_error_response(self, body):
            self._result = EndpointResponse(
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

    return TestAuthorizedHandler


@patch('jwt.decode', return_value={'username': 'user'})
def test_handler_proceeds_when_authorized(mock_jwt, test_auth_handler):
    th = test_auth_handler()
    th.receive(AuthorizedRequest(
        method='GET',
        resource='/resource/requiring/authorization',
        auth_token=AuthorizationToken(
            token='token',
            presenter='user'
            )
        ))
    assert th.result == EndpointResponse(
            code=status.HTTP_200_OK
            )
    assert th.status == EndpointHandlerStatus.COMPLETE


@patch('jwt.decode', return_value={'username': 'imposter'})
def test_handler_fails_when_ownership_is_falsified(mock_jwt, test_auth_handler):
    th = test_auth_handler()
    th.receive(AuthorizedRequest(
        method='GET',
        resource='/resource/requiring/authorization',
        auth_token=AuthorizationToken(
            token='token',
            presenter='user'
            )
        ))
    assert th.result == AccessDenied(
            code=status.HTTP_401_UNAUTHORIZED,
            msg="Cannot verify ownership of token."
            )
    assert th.status == EndpointHandlerStatus.ERROR


@patch('jwt.decode', side_effect=jwt.exceptions.InvalidTokenError)
def test_handler_fails_when_token_is_invalid(mock_jwt, test_auth_handler):
    th = test_auth_handler()
    th.receive(AuthorizedRequest(
        method='GET',
        resource='/resource/requiring/authorization',
        auth_token=AuthorizationToken(
            token='token',
            presenter='user'
            )
        ))
    assert th.result == AccessDenied(
            code=status.HTTP_401_UNAUTHORIZED,
            msg="Invalid token presented."
            )
    assert th.status == EndpointHandlerStatus.ERROR


@patch('jwt.decode', return_value={'username': 'user'})
def test_concrete_handler_errors_are_reported_after_authorization(mock_jwt, test_auth_handler):
    th = test_auth_handler()
    with patch.object(
            type(th),
            '_do_data_ops',
            side_effect=IdeaBankEndpointHandlerException
            ):
        th.receive(AuthorizedRequest(
            method='GET',
            resource='/resource/requiring/authorization',
            auth_token=AuthorizationToken(
                token='token',
                presenter='user'
                )
            ))
        assert th.status == EndpointHandlerStatus.ERROR
        assert th.result == EndpointResponse(
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
