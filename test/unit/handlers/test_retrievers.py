"""Tests for retrieval handlers"""

import pytest
import secrets
import hashlib
import datetime
import treelib
from unittest.mock import patch
from ideabank_webapi.handlers import EndpointHandlerStatus
from ideabank_webapi.handlers.retrievers import (
        AuthenticationHandler,
        ProfileRetrievalHandler,
        SpecificConceptRetrievalHandler,
        ConceptSearchResultHandler,
        ConceptLineageHandler,
        CheckFollowingStatusHandler,
        CheckLikingStatusHandler
        )
from ideabank_webapi.services import (
        RegisteredService,
        AccountsDataService,
        ConceptsDataService,
        EngagementDataService,
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
        ConceptLinkRecord,
        ConceptLineage,
        AccountFollowingRecord,
        ConceptLikingRecord,
        EndpointErrorMessage,
        EndpointInformationalMessage
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


@pytest.fixture
def test_lineage():
    t = treelib.Tree()
    t.create_node(
            tag='testuser/old-idea',
            identifier='testuser/old-idea',
            data=ConceptSimpleView(
                identifier='testuser/old-idea',
                thumbnail_url='http://example.com/thumbnails/testuser/old-idea'
                )
            )
    t.create_node(
            tag='testuser/new-idea',
            identifier='testuser/new-idea',
            parent='testuser/old-idea',
            data=ConceptSimpleView(
                identifier='testuser/new-idea',
                thumbnail_url='http://example.com/thumbnails/testuser/new-idea'
                )
            )
    t.create_node(
            tag='anotheruser/helpful-suggestion',
            identifier='anotheruser/helpful-suggestion',
            parent='testuser/new-idea',
            data=ConceptSimpleView(
                identifier='anotheruser/helpful-suggestion',
                thumbnail_url='http://example.com/thumbnails/anotheruser/helpful-suggestion'
                )
            )
    t.create_node(
            tag='someotheruser/a-little-improvement',
            identifier='someotheruser/a-little-improvement',
            parent='testuser/new-idea',
            data=ConceptSimpleView(
                identifier='someotheruser/a-little-improvement',
                thumbnail_url='http://example.com/thumbnails/someotheruser/a-little-improvement'
                )
            )
    return t


@pytest.fixture
def test_following_record():
    return AccountFollowingRecord(
            follower='user-a',
            followee='user-b'
            )


@pytest.fixture
def test_liking_record():
    return ConceptLikingRecord(
            user_liking='someuser',
            concept_liked='testuser/sample-idea'
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


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestConceptLineageHandler:

    def setup_method(self):
        self.handler = ConceptLineageHandler()
        self.handler.use_service(RegisteredService.CONCEPTS_DS, ConceptsDataService())

    @patch.object(
            S3Crud,
            'share_item',
            side_effect=(lambda key: f'http://example.com/{key}')
            )
    def test_successful_lineage_retrieval(
            self,
            mock_s3_url,
            mock_query_results,
            mock_query,
            test_simple_concept_view,
            test_lineage
            ):
        mock_query_results.one.return_value = test_simple_concept_view
        mock_query_results.all.side_effect = [
                [ConceptLinkRecord(ancestor='testuser/old-idea', descendant='testuser/new-idea')],
                [
                    ConceptLinkRecord(ancestor='testuser/new-idea', descendant='someotheruser/a-little-improvement'),
                    ConceptLinkRecord(ancestor='testuser/new-idea', descendant='anotheruser/helpful-suggestion')
                    ]
                ]
        self.handler.receive(ConceptRequest(
            author='testuser',
            title='new-idea',
            simple=True
            ))
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == ConceptLineage(
                nodes=test_lineage.size(),
                lineage=test_lineage.to_dict(with_data=True)
                )

    def test_retrieval_of_lineage_where_focus_does_not_exist(
            self,
            mock_query_results,
            mock_query
            ):
        mock_query_results.one.side_effect = NoResultFound
        self.handler.receive(ConceptRequest(
            author='testuser',
            title='fake-idea',
            simple=True
            ))
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_404_NOT_FOUND
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg="Could not build the lineage for testuser/fake-idea"
                )

    @patch.object(
            ConceptLineageHandler,
            '_do_data_ops',
            side_effect=BaseIdeaBankAPIException("Really obscure error")
        )
    def test_a_really_messed_up_scenario(
            self,
            mock_data_ops,
            mock_query_results,
            mock_query
            ):
        self.handler.receive(ConceptRequest(
            author='testuser',
            title='fake-idea',
            simple=True
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
class TestFollowStatusHandler:

    def setup_method(self):
        self.handler = CheckFollowingStatusHandler()
        self.handler.use_service(RegisteredService.ENGAGE_DS, EngagementDataService())

    def test_check_affirms_following_status(
            self,
            mock_query_results,
            mock_query,
            test_following_record
            ):
        mock_query_results.one.return_value == test_following_record
        self.handler.receive(test_following_record)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == EndpointInformationalMessage(
                msg=f"{test_following_record.follower} is following {test_following_record.followee}"
                )

    def test_check_denies_following_status(
            self,
            mock_query_results,
            mock_query,
            test_following_record
            ):
        mock_query_results.one.side_effect = NoResultFound
        self.handler.receive(test_following_record)
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_404_NOT_FOUND
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg=f"{test_following_record.follower} is not following {test_following_record.followee}"
                )

    @patch.object(
            CheckFollowingStatusHandler,
            '_do_data_ops',
            side_effect=BaseIdeaBankAPIException("Really obscure error")
        )
    def test_a_really_messed_up_scenario(
            self,
            mock_data_ops,
            mock_query_results,
            mock_query,
            test_following_record
            ):
        self.handler.receive(test_following_record)
        mock_data_ops.assert_called_once()
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestLikeStatusHandler:

    def setup_method(self):
        self.handler = CheckLikingStatusHandler()
        self.handler.use_service(RegisteredService.ENGAGE_DS, EngagementDataService())

    def test_check_affirms_liking_status(
            self,
            mock_query_results,
            mock_query,
            test_liking_record
            ):
        mock_query_results.one.return_value == test_liking_record
        self.handler.receive(test_liking_record)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == EndpointInformationalMessage(
                msg=f"{test_liking_record.user_liking} does like {test_liking_record.concept_liked}"
                )

    def test_check_denies_liking_status(
            self,
            mock_query_results,
            mock_query,
            test_liking_record
            ):
        mock_query_results.one.side_effect = NoResultFound
        self.handler.receive(test_liking_record)
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_404_NOT_FOUND
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg=f"{test_liking_record.user_liking} does not like {test_liking_record.concept_liked}"
                )

    @patch.object(
            CheckLikingStatusHandler,
            '_do_data_ops',
            side_effect=BaseIdeaBankAPIException("Really obscure error")
        )
    def test_a_really_messed_up_scenario(
            self,
            mock_data_ops,
            mock_query_results,
            mock_query,
            test_liking_record
            ):
        self.handler.receive(test_liking_record)
        mock_data_ops.assert_called_once()
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )
