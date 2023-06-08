"""Tests for retrieval handlers"""

import pytest
import faker
import random
import datetime
import treelib
import uuid
from unittest.mock import patch
from ideabank_webapi.handlers import EndpointHandlerStatus
from ideabank_webapi.handlers.retrievers import (
        AuthenticationHandler,
        ProfileRetrievalHandler,
        SpecificConceptRetrievalHandler,
        ConceptSearchResultHandler,
        ConceptLineageHandler,
        CheckFollowingStatusHandler,
        CheckLikingStatusHandler,
        ConceptCommentsSectionHandler,
        )
from ideabank_webapi.services import (
        RegisteredService,
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
        ConceptComment,
        ConceptCommentThreads,
        EndpointErrorMessage,
        EndpointInformationalMessage
)
from ideabank_webapi.models.schema import Comments, Accounts
from ideabank_webapi.exceptions import BaseIdeaBankAPIException

from sqlalchemy import create_engine
from sqlalchemy.exc import NoResultFound
from fastapi import status


@pytest.fixture
def test_creds_set(test_auth_projection):
    return CredentialSet(
            display_name=test_auth_projection.display_name,
            password='supersecretpassword'
            )


@pytest.fixture
def test_auth_projection(test_auth_token):
    return Accounts(
            display_name=test_auth_token.presenter,
            password_hash='h4shh4sh',
            salt_value='s4l7y'
            )


@pytest.fixture
def test_profile_projection(faker):
    return Accounts(
            preferred_name=faker.name(),
            biography=faker.paragraph(nb_sentences=random.randint(2, 10)),
            )


@pytest.fixture
def test_full_concept_view(test_concept_simple_view, faker):
    return ConceptFullView(
            author=test_concept_simple_view.identifier.split('/')[0],
            title=test_concept_simple_view.identifier.split('/')[1],
            description=faker.sentence(),
            diagram='{}',
            thumbnail_url='http://example.com/thumbnails/'
                          f"{test_concept_simple_view.identifier.split('/')[0]}/"
                          f"{test_concept_simple_view.identifier.split('/')[1]}"
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
def test_following_record(faker):
    return AccountFollowingRecord(
            follower=faker.user_name(),
            followee=faker.user_name()
            )


@pytest.fixture
def test_liking_record(faker):
    return ConceptLikingRecord(
            user_liking=faker.user_name(),
            concept_liked=f'{faker.user_name()}/{faker.domain_word()}'
            )


@pytest.fixture(scope='session')
def test_existing_comment_thread():
    return ConceptCommentThreads(
            threads=[
                ConceptComment(
                    comment_id=uuid.uuid4(),
                    comment_author='testuser',
                    comment_text='thread #1',
                    responses=[
                        ConceptComment(
                            comment_id=uuid.uuid4(),
                            comment_author='someuser',
                            comment_text='thread #1.1',
                            responses=[]
                            ),
                        ConceptComment(
                            comment_id=uuid.uuid4(),
                            comment_author='anotheruser',
                            comment_text='thread #1.2',
                            responses=[]
                            )
                        ]
                    ),
                ConceptComment(
                    comment_id=uuid.uuid4(),
                    comment_author='someotheruser',
                    comment_text='thread#2',
                    responses=[]
                    )
                ]
            )


@pytest.fixture
def test_empty_comment_thread():
    return ConceptCommentThreads(threads=[])


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestAccountAuthenticationHandler:

    def setup_method(self):
        self.handler = AuthenticationHandler()
        self.handler.use_service(RegisteredService.ACCOUNTS_DS)

    @patch('jwt.encode')
    @patch('secrets.compare_digest', return_value=True)
    def test_successful_user_authentication(
            self,
            mock_digest,
            mock_jwt,
            mock_query_results,
            mock_query,
            test_auth_projection,
            test_auth_token,
            test_creds_set
            ):
        print(test_auth_token.token)
        mock_query_results.one.return_value = test_auth_projection
        mock_jwt.return_value = test_auth_token.token
        self.handler.receive(test_creds_set)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == test_auth_token

    @patch('secrets.compare_digest', return_value=False)
    def test_unsuccessful_user_authentication(
            self,
            mock_secrets,
            mock_query_results,
            mock_query,
            test_creds_set,
            test_auth_projection
            ):
        mock_query_results.one.return_value = test_auth_projection
        self.handler.receive(test_creds_set)
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_401_UNAUTHORIZED
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Invalid display name or password'
                )

    def test_no_such_user_authentication(
            self,
            mock_query_results,
            mock_query,
            test_creds_set
            ):
        mock_query_results.one.side_effect = NoResultFound
        self.handler.receive(test_creds_set)
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
            mock_query,
            test_creds_set
            ):
        self.handler.receive(test_creds_set)
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
        self.handler.use_service(RegisteredService.ACCOUNTS_DS)

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
            test_creds_set,
            test_profile_projection
            ):
        mock_query_results.one.return_value = test_profile_projection
        self.handler.receive(test_creds_set.display_name)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == ProfileView(
                preferred_name=test_profile_projection.preferred_name,
                biography=test_profile_projection.biography,
                avatar_url=f'http://example.com/avatars/{test_creds_set.display_name}'
                )

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
            test_creds_set
            ):
        self.handler.receive(test_creds_set.display_name)
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
        self.handler.use_service(RegisteredService.CONCEPTS_DS)

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
            test_concept_simple_view,
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
        assert self.handler.result.body == test_concept_simple_view if simple else test_full_concept_view

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
        self.handler.use_service(RegisteredService.CONCEPTS_DS)

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
            test_concept_simple_view
            ):
        mock_query_results.all.return_value = 10 * [test_concept_simple_view]
        self.handler.receive(ConceptSearchQuery(
                author=test_concept_simple_view.identifier.split('/')[0],
                title=test_concept_simple_view.identifier.split('/')[1],
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
            test_concept_simple_view
            ):
        self.handler.receive(ConceptSearchQuery(
                author=test_concept_simple_view.identifier.split('/')[0],
                title=test_concept_simple_view.identifier.split('/')[1],
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
            test_concept_simple_view
            ):
        mock_query_results.all.return_value = []
        self.handler.receive(ConceptSearchQuery(
                author=test_concept_simple_view.identifier.split('/')[0],
                title=test_concept_simple_view.identifier.split('/')[1],
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
        self.handler.use_service(RegisteredService.CONCEPTS_DS)

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
            test_concept_simple_view,
            test_lineage
            ):
        mock_query_results.one.return_value = test_concept_simple_view
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
        self.handler.use_service(RegisteredService.ENGAGE_DS)

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
        self.handler.use_service(RegisteredService.ENGAGE_DS)

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


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestCommentSectionHandler:

    def setup_method(self):
        self.handler = ConceptCommentsSectionHandler()
        self.handler.use_service(RegisteredService.ENGAGE_DS)

    def test_obtain_existing_comment_thread(
            self,
            mock_query_results,
            mock_query,
            test_existing_comment_thread
            ):
        mock_query_results.all.side_effect = [
                [
                    Comments(
                        comment_id=c.comment_id,
                        comment_by=c.comment_author,
                        free_text=c.comment_text
                        )
                    for c in test_existing_comment_thread.threads
                    ],
                [
                    Comments(
                        comment_id=c.comment_id,
                        comment_by=c.comment_author,
                        free_text=c.comment_text
                        )
                    for c in test_existing_comment_thread.threads[0].responses
                    ],
                [
                    Comments(
                        comment_id=c.comment_id,
                        comment_by=c.comment_author,
                        free_text=c.comment_text
                        )
                    for c in test_existing_comment_thread.threads[1].responses
                    ],
                test_existing_comment_thread.threads[0].responses[0].responses,
                test_existing_comment_thread.threads[0].responses[1].responses
                ]
        self.handler.receive(ConceptRequest(
            author='testuser',
            title='sample-idea',
            simple=True
            ))
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == test_existing_comment_thread

    def test_obtain_blank_comment_thread(
            self,
            mock_query_results,
            mock_query,
            test_empty_comment_thread
            ):
        mock_query_results.all.side_effect = [[]]
        self.handler.receive(ConceptRequest(
            author='testuser',
            title='sample-idea',
            simple=True
            ))
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_200_OK
        assert self.handler.result.body == test_empty_comment_thread

    @patch.object(
            ConceptCommentsSectionHandler,
            '_do_data_ops',
            side_effect=BaseIdeaBankAPIException("Really obscure error")
        )
    def test_a_really_messed_up_scenario(
            self,
            mock_data_ops,
            mock_query_results,
            mock_query,
            ):
        self.handler.receive(ConceptRequest(
            author='testuser',
            title='sample-idea',
            simple=True
            ))
        mock_data_ops.assert_called_once()
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )
