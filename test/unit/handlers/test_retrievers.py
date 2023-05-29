"""Tests for retrieval handlers"""

import pytest
import secrets
import hashlib
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
        AccountRecord,
        AuthorizationToken,
        ProfileView,
        EndpointErrorMessage,
        IdeaBankSchema,
)
from ideabank_webapi.exceptions import BaseIdeaBankAPIException

from sqlalchemy import create_engine
from sqlalchemy.exc import NoResultFound
from fastapi import status
import jwt


@pytest.fixture
def test_valid_credential_set():
    return CredentialSet(
            display_name='testuser',
            password='testpassword'
            )


@pytest.fixture
def test_account_record(scope='session'):
    salt = secrets.token_hex()
    hashed = hashlib.sha256(
            f'testpassword{salt}'.encode('utf-8')
            ).hexdigest()
    return AccountRecord(
            display_name='testuser',
            password_hash=hashed,
            salt_value=salt
            )


@pytest.fixture
def test_profile_view(scope='session'):
    return ProfileView(
            preferred_name='a real name',
            biography='A short version of my life story',
            avatar_url='http://example.com/avatars/testuser'
            )


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestAccountAuthenticationHandler:

    def setup_method(self):
        self.handler = AuthenticationHandler()
        self.handler.use_service(RegisteredService.ACCOUNTS_DS, AccountsDataService())

    @patch('jwt.encode', return_value="testtoken")
    def test_successful_user_authentication(
            self,
            mock_jwt,
            mock_query_results,
            mock_query,
            test_valid_credential_set,
            test_account_record
            ):
        mock_query_results.one.return_value = test_account_record
        self.handler.receive(test_valid_credential_set)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == AuthorizationToken(
                token='testtoken',
                presenter=test_account_record.display_name
                )

    @patch('secrets.compare_digest', return_value=False)
    def test_unsuccessful_user_authentication(
            self,
            mock_secrets,
            mock_query_results,
            mock_query,
            test_valid_credential_set,
            test_account_record
            ):
        mock_query_results.one.return_value = test_account_record
        self.handler.receive(test_valid_credential_set)
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_401_UNAUTHORIZED
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Invalid display name or password'
                )

    def test_no_such_user_authentication(
            self,
            mock_query_results,
            mock_query,
            test_valid_credential_set,
            test_account_record
            ):
        mock_query_results.one.side_effect = NoResultFound
        self.handler.receive(test_valid_credential_set)
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
    def test_a_really_messed_up_scenario(
            self,
            mock_data_ops,
            mock_query_results,
            mock_query
            ):
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
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestProfileRetrievalHandler:

    def setup_method(self):
        self.handler = ProfileRetrievalHandler()
        self.handler.use_service(RegisteredService.ACCOUNTS_DS, AccountsDataService())

    @patch.object(
            S3Crud,
            'share_item',
            side_effect=(lambda key: f'http://example.com/{key}')
        )
    def test_successful_profile_retrieval(
            self,
            mock_share,
            mock_query_results,
            mock_query,
            test_account_record,
            test_profile_view
            ):
        mock_query_results.one.return_value = test_profile_view
        self.handler.receive(test_account_record.display_name)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == test_profile_view

    @pytest.mark.parametrize("username", [
        'notauser',
        'mysteryuser'
        ])
    def test_unsuccessful_profile_retrieval(
            self,
            mock_query_results,
            mock_query,
            username,
            ):
        mock_query_results.one.side_effect = NoResultFound
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
    def test_a_really_messed_up_scenario(
            self,
            mock_data_ops,
            mock_query_results,
            mock_query,
            test_account_record
            ):
        self.handler.receive(test_account_record.display_name)
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )
