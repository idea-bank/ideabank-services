"""Tests for eraser endpoint handler"""

import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from fastapi import status
from ideabank_webapi.handlers import EndpointHandlerStatus
from ideabank_webapi.handlers.erasers import (
        StopFollowingAccountHandler
        )
from ideabank_webapi.handlers.preprocessors import AuthorizationRequired
from ideabank_webapi.services import (
        QueryService,
        EngagementDataService,
        RegisteredService
        )
from ideabank_webapi.models import (
        AccountFollowingRecord,
        UnfollowRequest,
        AuthorizationToken,
        EndpointInformationalMessage,
        EndpointErrorMessage,
        EndpointResponse
        )
from ideabank_webapi.exceptions import NotAuthorizedError, BaseIdeaBankAPIException


@pytest.fixture
def test_auth_token():
    return AuthorizationToken(
            token='testtoken',
            presenter='testuser'
            )


@pytest.fixture
def test_unfollow_request(test_auth_token):
    return UnfollowRequest(
            auth_token=test_auth_token,
            follower='user-a',
            followee='user-b'
            )


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestAccountCreationHandler:

    def setup_method(self):
        self.handler = StopFollowingAccountHandler()
        self.handler.use_service(RegisteredService.ENGAGE_DS, EngagementDataService())

    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_processing_unfollow_request(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_unfollow_request
            ):
        self.handler.receive(test_unfollow_request)
        self.handler.status == EndpointHandlerStatus.COMPLETE
        self.handler.result.code == status.HTTP_200_OK
        self.handler.result.body == EndpointInformationalMessage(
                msg=f"{test_unfollow_request.follower} is no longer following {test_unfollow_request.followee}"
                )

    @pytest.mark.parametrize("err_type, err_msg", [
        (NotAuthorizedError, 'Invalid token presented'),
        (NotAuthorizedError, 'Unable to verify token ownership')
        ])
    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_unauthorized_unfollow_request(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_unfollow_request,
            err_type,
            err_msg
            ):
        mock_auth_check.side_effect = err_type(err_msg)
        self.handler.receive(test_unfollow_request)
        self.handler.status == EndpointHandlerStatus.ERROR
        self.handler.result.code == status.HTTP_401_UNAUTHORIZED
        self.handler.result.body == EndpointErrorMessage(err_msg=err_msg)

    @patch.object(
            StopFollowingAccountHandler,
            '_do_data_ops',
            side_effect=BaseIdeaBankAPIException("Really obscure error")
        )
    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_a_really_messed_up_scenario(
            self,
            mock_auth_check,
            mock_data_ops,
            mock_query_result,
            mock_query,
            test_unfollow_request
            ):
        self.handler.receive(test_unfollow_request)
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )
