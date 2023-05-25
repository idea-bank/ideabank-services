"""Tests for guard endpoints classes"""

from ideabank_webapi.handlers import EndpointHandlerStatus
from ideabank_webapi.handlers.preprocessors import AuthorizationRequired
from ideabank_webapi.models.artifacts import AuthorizationToken
from ideabank_webapi.models.responses import EndpointSuccessResponse, EndpointErrorResponse
from ideabank_webapi.models.payloads import AuthorizedPayload
from ideabank_webapi.exceptions import IdeaBankEndpointHandlerException


import pytest
from fastapi import status
import jwt
from unittest.mock import patch


@pytest.fixture
def test_auth_handler():
    class TestAuthorizedHandler(AuthorizationRequired):

        def _do_data_ops(self, request):
            return {'number': 1}

        def _build_success_response(self, body):
            self._result = EndpointSuccessResponse(
                    code=status.HTTP_200_OK,
                    msg='Authorized request completed.'
                    )

        def _build_error_response(self, body):
            self._result = EndpointErrorResponse(
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    err_msg='Authorized request could not be completed.'
                    )

    return TestAuthorizedHandler


@patch('jwt.decode', return_value={'username': 'user'})
def test_handler_proceeds_when_authorized(mock_jwt, test_auth_handler):
    th = test_auth_handler()
    th.receive(AuthorizedPayload(
        auth_token=AuthorizationToken(
            token='token',
            presenter='user'
            ))
        )
    assert th.result == EndpointSuccessResponse(
            code=status.HTTP_200_OK,
            msg='Authorized request completed.'
            )
    assert th.status == EndpointHandlerStatus.COMPLETE


@patch('jwt.decode', return_value={'username': 'imposter'})
def test_handler_fails_when_ownership_is_falsified(mock_jwt, test_auth_handler):
    th = test_auth_handler()
    th.receive(AuthorizedPayload(
        auth_token=AuthorizationToken(
            token='token',
            presenter='user'
            ))
        )
    assert th.result == EndpointErrorResponse(
            code=status.HTTP_401_UNAUTHORIZED,
            msg="Cannot verify ownership of token."
            )
    assert th.status == EndpointHandlerStatus.ERROR


@patch('jwt.decode', side_effect=jwt.exceptions.InvalidTokenError)
def test_handler_fails_when_token_is_invalid(mock_jwt, test_auth_handler):
    th = test_auth_handler()
    th.receive(AuthorizedPayload(
        auth_token=AuthorizationToken(
            token='token',
            presenter='user'
            ))
        )
    assert th.result == EndpointErrorResponse(
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
        th.receive(AuthorizedPayload(
            auth_token=AuthorizationToken(
                token='token',
                presenter='user'
                )
            ))
        assert th.status == EndpointHandlerStatus.ERROR
        assert th.result == EndpointErrorResponse(
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    err_msg='Authorized request could not be completed.'
                    )
