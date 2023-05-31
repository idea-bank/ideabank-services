"""Tests for retrieval handlers"""

import pytest
import secrets
import hashlib
import datetime
from unittest.mock import patch
from ideabank_webapi.handlers import EndpointHandlerStatus
from ideabank_webapi.handlers.retrievers import (
        AuthenticationHandler,
        ProfileRetrievalHandler,
        SpecificConceptRetrievalHandler,
        ConceptSearchResultHandler
        )
from ideabank_webapi.services import (
        RegisteredService,
        AccountsDataService,
        ConceptsDataService,
        QueryService,
        S3Crud
        )
from ideabank_webapi.models import (
        CredentialSet,
        AccountRecord,
        AuthorizationToken,
        ProfileView,
        ConceptRequest,
        ConceptFullView,
        ConceptSearchQuery,
        ConceptSimpleView,
        EndpointErrorMessage,
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


@pytest.fixture
def test_simple_concept_view():
    return ConceptSimpleView(
            identifier='testuser/sample-idea',
            thumbnail_url='http://example.com/thumbnails/testuser/sample-idea'
            )


@pytest.fixture
def test_full_concept_view():
    return ConceptFullView(
            author='testuser',
            title='sample-idea',
            description='This is a explanation of the sample idea',
            diagram={},
            thumbnail_url='http://example.com/thumbnails/testuser/sample-idea'
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


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestSpecificConceptRetrievalHandler:

    def setup_method(self):
        self.handler = SpecificConceptRetrievalHandler()
        self.handler.use_service(RegisteredService.CONCEPTS_DS, ConceptsDataService())

    @pytest.mark.parametrize("simple", [
        True,
        False
    ])
    @patch.object(
            S3Crud,
            'share_item',
            side_effect=(lambda key: f'http://example.com/{key}')
        )
    def test_successful_concept_retrieval(
            self,
            mock_s3_url,
            mock_query_results,
            mock_query,
            test_full_concept_view,
            test_simple_concept_view,
            simple
            ):
        mock_query_results.one.return_value = test_full_concept_view
        self.handler.receive(ConceptRequest(
            author=test_full_concept_view.author,
            title=test_full_concept_view.title,
            simple=simple
            ))
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == test_simple_concept_view if simple else test_full_concept_view

    @pytest.mark.parametrize("simple", [
        True,
        False
    ])
    def test_unsuccessful_concept_retrieval(
            self,
            mock_query_results,
            mock_query,
            test_full_concept_view,
            simple
            ):
        mock_query_results.one.side_effect = NoResultFound
        self.handler.receive(ConceptRequest(
            author=test_full_concept_view.author,
            title=test_full_concept_view.title,
            simple=simple
            ))
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_404_NOT_FOUND
        assert self.handler.result.body == EndpointErrorMessage(
            err_msg=f'No match for `{test_full_concept_view.author}/{test_full_concept_view.title}`'
                )

    @pytest.mark.parametrize("simple", [
        True,
        False
        ])
    @patch.object(
            SpecificConceptRetrievalHandler,
            '_do_data_ops',
            side_effect=BaseIdeaBankAPIException("Really obscure error")
        )
    def test_a_really_messed_up_scenario(
            self,
            mock_data_ops,
            mock_query_results,
            mock_query,
            test_full_concept_view,
            simple
            ):
        self.handler.receive(ConceptRequest(
            author=test_full_concept_view.author,
            title=test_full_concept_view.title,
            simple=simple
            )
        )
        mock_data_ops.assert_called_once()
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestConceptSearchHandler:

    def setup_method(self):
        self.handler = ConceptSearchResultHandler()
        self.handler.use_service(RegisteredService.CONCEPTS_DS, ConceptsDataService())

    @patch.object(
            S3Crud,
            'share_item',
            side_effect=(lambda key: f'http://example.com/{key}')
            )
    def test_successful_search_result_retrieval(
            self,
            mock_s3_url,
            mock_query_results,
            mock_query,
            test_simple_concept_view
            ):
        mock_query_results.all.return_value = 10 * [test_simple_concept_view]
        self.handler.receive(ConceptSearchQuery(
                author=test_simple_concept_view.identifier.split('/')[0],
                title=test_simple_concept_view.identifier.split('/')[1],
                not_before=datetime.datetime.fromtimestamp(0, datetime.timezone.utc),
                not_after=datetime.datetime.now(datetime.timezone.utc)
            ))
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == mock_query_results.all.return_value

    @patch.object(
            ConceptSearchResultHandler,
            '_do_data_ops',
            side_effect=BaseIdeaBankAPIException("Really obscure error")
        )
    def test_a_really_messed_up_scenario(
            self,
            mock_data_ops,
            mock_query_results,
            mock_query,
            test_simple_concept_view
            ):
        self.handler.receive(ConceptSearchQuery(
                author=test_simple_concept_view.identifier.split('/')[0],
                title=test_simple_concept_view.identifier.split('/')[1],
                not_before=datetime.datetime.fromtimestamp(0, datetime.timezone.utc),
                not_after=datetime.datetime.now(datetime.timezone.utc)
            ))
        mock_data_ops.assert_called_once()
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )

    @patch.object(
            S3Crud,
            'share_item',
            side_effect=(lambda key: f'http://example.com/{key}')
            )
    def test_no_results_is_not_an_error(
            self,
            mock_s3_url,
            mock_query_results,
            mock_query,
            test_simple_concept_view
            ):
        mock_query_results.all.return_value = []
        self.handler.receive(ConceptSearchQuery(
                author=test_simple_concept_view.identifier.split('/')[0],
                title=test_simple_concept_view.identifier.split('/')[1],
                not_before=datetime.datetime.fromtimestamp(0, datetime.timezone.utc),
                not_after=datetime.datetime.now(datetime.timezone.utc)
            ))
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == mock_query_results.all.return_value
