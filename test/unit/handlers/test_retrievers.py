"""Tests for retrieval handlers"""

import pytest
from unittest.mock import patch
from ideabank_webapi.handlers import EndpointHandlerStatus
from ideabank_webapi.handlers.retrievers import (
        AuthenticationHandler,
        ProfileRetrievalHandler
        )
from ideabank_webapi.handlers.creators import AccountCreationHandler
from ideabank_webapi.services import RegisteredService, AccountsDataService, QueryService, S3Crud
from ideabank_webapi.models import (
        CredentialSet,
        AuthorizationToken,
        ProfileView,
        EndpointInformationalMessage,
        EndpointErrorMessage,
        IdeaBankSchema,
        Accounts
)
from ideabank_webapi.exceptions import BaseIdeaBankAPIException

from sqlalchemy import create_engine
from fastapi import status
import jwt


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
class TestAccountAuthenticationHandler:
    TEST_ACCOUNTS = [
        CredentialSet(display_name=f'username{i}', password=f'password{i}')
        for i in range(1, 6)
            ]

    def setup_method(self):
        self.handler = AuthenticationHandler()
        self.handler.use_service(RegisteredService.ACCOUNTS_DS, AccountsDataService())

    def _init_test_db(self):
        IdeaBankSchema.metadata.create_all(
                self.handler.get_service(RegisteredService.ACCOUNTS_DS).ENGINE
                )
        for user in self.TEST_ACCOUNTS:
            account_maker = AccountCreationHandler()
            account_maker.use_service(RegisteredService.ACCOUNTS_DS, AccountsDataService())
            account_maker.receive(user)

    @pytest.mark.parametrize("credentials", [
        CredentialSet(display_name=f'username{i}', password=f'password{i}')
        for i in range(1, 6)
        ])
    @patch('jwt.encode', return_value="testtoken")
    def test_successful_user_authentication(self, mock_jwt, credentials):
        self._init_test_db()
        self.handler.receive(credentials)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == AuthorizationToken(
                token='testtoken',
                presenter=credentials.display_name
                )

    @pytest.mark.parametrize("credentials", [
        CredentialSet(display_name='notauser', password='nobodycares'),  # User does not exist
        CredentialSet(display_name='username1', password='nottherightpassword')  # Wrong password
        ])
    @patch('jwt.encode', return_value='testtoken')
    def test_unsuccessful_user_authentication(self, mock_jwt, credentials):
        self._init_test_db()
        self.handler.receive(credentials)
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_401_UNAUTHORIZED
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Invalid display name or password'
                )

    @patch.object(
            AuthenticationHandler,
            '_do_data_ops',
            side_effect=BaseIdeaBankAPIException("Really obscure error")
        )
    def test_a_really_messed_up_scenario(self, mock_data_ops):
        self.handler.receive(CredentialSet(
            display_name='unluckyuser',
            password='unluckypassword'
            ))
        mock_data_ops.assert_called_once()
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
class TestProfileRetrievalHandler:
    TEST_ACCOUNTS = [
        CredentialSet(display_name=f'username{i}', password=f'password{i}')
        for i in range(1, 6)
            ]

    def setup_method(self):
        self.handler = ProfileRetrievalHandler()
        self.handler.use_service(RegisteredService.ACCOUNTS_DS, AccountsDataService())

    def _init_test_db(self):
        IdeaBankSchema.metadata.create_all(
                self.handler.get_service(RegisteredService.ACCOUNTS_DS).ENGINE
                )
        for user in self.TEST_ACCOUNTS:
            account_maker = AccountCreationHandler()
            account_maker.use_service(RegisteredService.ACCOUNTS_DS, AccountsDataService())
            account_maker.receive(user)

    @pytest.mark.parametrize("username", [
        f'username{i}' for i in range(1, 6)
        ])
    @patch.object(
            S3Crud,
            'share_item',
            side_effect=(lambda key: f'http://example.com/{key}')
        )
    def test_successful_profile_retrieval(self, mock_share, username):
        self._init_test_db()
        self.handler.receive(username)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == ProfileView(
                preferred_name=username,
                biography=f"{username} hasn't added a bio.",
                avatar_url=f'http://example.com/avatars/{username}'
                )

    @pytest.mark.parametrize("username", [
        'notauser',
        'mysteryuser'
        ])
    @patch.object(
            S3Crud,
            'share_item',
            side_effect=(lambda key: f'http://example.com/avatars/{key}')
            )
    def test_unsuccessful_profile_retrieval(self, mock_share, username):
        self._init_test_db()
        self.handler.receive(username)
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_404_NOT_FOUND
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg=f'Profile for {username} is not available'
                )

    @patch.object(
            ProfileRetrievalHandler,
            '_do_data_ops',
            side_effect=BaseIdeaBankAPIException("Really obscure error")
        )
    def test_a_really_messed_up_scenario(self, mock_data_ops):
        self.handler.receive(CredentialSet(
            display_name='unluckyuser',
            password='unluckypassword'
            ))
        mock_data_ops.assert_called_once()
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )


