"""Tests for guard endpoints classes"""

from ideabank_webapi.handlers import EndpointHandlerStatus
from ideabank_webapi.handlers.preprocessors import AuthorizationRequired
from ideabank_webapi.models.artifacts import AuthorizationToken, EndpointResponse
from ideabank_webapi.models.artifacts import EndpointInformationalMessage, EndpointErrorMessage
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

        def _build_success_response(self, requested_data):
            self._result = EndpointResponse(
                    code=status.HTTP_200_OK,
                    body=EndpointInformationalMessage(
                        msg='Authorized request completed.'
                        )
                    )

        def _build_error_response(self, exc):
            self._result = EndpointResponse(
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    body=EndpointErrorMessage(
                        err_msg='Authorized request could not be completed.'
                        )
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
    assert th.status == EndpointHandlerStatus.COMPLETE
    assert th.result.code == status.HTTP_200_OK
    assert th.result.body == EndpointInformationalMessage(
            msg='Authorized request completed.'
            )


@patch('jwt.decode', return_value={'username': 'imposter'})
def test_handler_fails_when_ownership_is_falsified(mock_jwt, test_auth_handler):
    th = test_auth_handler()
    th.receive(AuthorizedPayload(
        auth_token=AuthorizationToken(
            token='token',
            presenter='user'
            ))
        )
    assert th.status == EndpointHandlerStatus.ERROR
    assert th.result.code == status.HTTP_401_UNAUTHORIZED
    assert th.result.body == EndpointErrorMessage(
            err_msg='Cannot verify ownership of token.'
            )


@patch('jwt.decode', side_effect=jwt.exceptions.InvalidTokenError)
def test_handler_fails_when_token_is_invalid(mock_jwt, test_auth_handler):
    th = test_auth_handler()
    th.receive(AuthorizedPayload(
        auth_token=AuthorizationToken(
            token='token',
            presenter='user'
            ))
        )
    assert th.status == EndpointHandlerStatus.ERROR
    assert th.result.code == status.HTTP_401_UNAUTHORIZED
    assert th.result.body == EndpointErrorMessage(
            err_msg='Invalid token presented.'
            )


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
        assert th.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert th.result.body == EndpointErrorMessage(
                err_msg='Authorized request could not be completed.'
                )
