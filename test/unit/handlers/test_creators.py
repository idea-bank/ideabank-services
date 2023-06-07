"""Tests for creator handlers"""

import pytest
import uuid
from unittest.mock import patch
from ideabank_webapi.handlers import EndpointHandlerStatus
from ideabank_webapi.handlers.creators import (
        AccountCreationHandler,
        ConceptCreationHandler,
        ConceptLinkingHandler,
        StartFollowingAccountHandler,
        StartLikingConceptHandler,
        CommentCreationHandler
        )
from ideabank_webapi.handlers.preprocessors import AuthorizationRequired
from ideabank_webapi.services import (
        RegisteredService,
        QueryService,
        S3Crud,
        )
from ideabank_webapi.models import (
        CredentialSet,
        EndpointInformationalMessage,
        EndpointErrorMessage,
        AuthorizationToken,
        ConceptSimpleView,
        ConceptDataPayload,
        CreateConcept,
        EstablishLink,
        ConceptLinkRecord,
        FollowRequest,
        AccountFollowingRecord,
        LikeRequest,
        CreateComment
)
from ideabank_webapi.models.schema import Likes
from ideabank_webapi.exceptions import (
        BaseIdeaBankAPIException,
        NotAuthorizedError,
        )

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from fastapi import status


@pytest.fixture
def test_auth_token():
    return AuthorizationToken(
            token='testtoken',
            presenter='testuser'
            )


@pytest.fixture
def test_concept_payload():
    return ConceptDataPayload(
            author='testuser',
            title='sample-idea',
            description='An example of a really cool idea',
            diagram={}
            )


@pytest.fixture
def test_concept_simple_view():
    return ConceptSimpleView(
            identifier='testuser/sample-idea',
            thumbnail_url='http://example.com/thumbnails/testuser/sample-idea'
            )


@pytest.fixture
def test_valid_credential_set():
    return CredentialSet(
            display_name='testuser',
            password='testpassword'
            )


@pytest.fixture
def test_linking_request():
    return ConceptLinkRecord(
            ancestor='testuser/sample-idea',
            descendant='anotheruser/derived-idea'
            )


@pytest.fixture
def test_follow_request(test_auth_token):
    return FollowRequest(
            auth_token=test_auth_token,
            follower='user-a',
            followee='user-b'
            )


@pytest.fixture
def test_like_request(test_auth_token):
    return LikeRequest(
            auth_token=test_auth_token,
            user_liking='someuser',
            concept_liked='testuser/sample-idea'
            )


@pytest.fixture
def test_start_new_thread(test_auth_token):
    return CreateComment(
            auth_token=test_auth_token,
            concept_id="testuser/sample-idea",
            comment_author="someuser",
            comment_text="this is a cool idea"
            )


@pytest.fixture
def test_responsd_in_thread(test_auth_token):
    return CreateComment(
            auth_token=test_auth_token,
            concept_id="testuser/sample-idea",
            comment_author="testuser",
            comment_text="Thank you",
            response_to=uuid.uuid4()
            )


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestAccountCreationHandler:

    def setup_method(self):
        self.handler = AccountCreationHandler()
        self.handler.use_service(RegisteredService.ACCOUNTS_DS)

    def test_create_new_account(
           self,
           mock_query_result,
           mock_query,
           test_valid_credential_set
           ):
        mock_query_result.one.return_value = test_valid_credential_set
        self.handler.receive(test_valid_credential_set)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_201_CREATED
        assert self.handler.result.body == EndpointInformationalMessage(
                msg=f'Account for {test_valid_credential_set.display_name} successfully created'
                )

    def test_attempt_to_create_duplicate_account(
            self,
            mock_query_result,
            mock_query,
            test_valid_credential_set
            ):
        mock_query.side_effect = IntegrityError("doing", "a", "test")
        self.handler.receive(test_valid_credential_set)
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_403_FORBIDDEN
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg=f'Account not created: {test_valid_credential_set.display_name} not available'
                )

    @patch.object(
            AccountCreationHandler,
            '_do_data_ops',
            side_effect=BaseIdeaBankAPIException("Really obscure error")
        )
    def test_a_really_messed_up_scenario(
            self,
            mock_data_ops,
            mock_query_result,
            mock_query
            ):
        self.handler.receive(CredentialSet(
            display_name='unluckyuser',
            password='unluckypassword'
            ))
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestConceptCreationHandler:

    def setup_method(self):
        self.handler = ConceptCreationHandler()
        self.handler.use_service(RegisteredService.CONCEPTS_DS)

    @patch.object(AuthorizationRequired, '_check_if_authorized')
    @patch.object(S3Crud, 'share_item')
    def test_successful_concept_creation(
        self,
        mock_s3_url,
        mock_auth_check,
        mock_query_result,
        mock_query,
        test_auth_token,
        test_concept_payload,
        test_concept_simple_view
    ):
        mock_query_result.one.return_value = test_concept_simple_view
        mock_s3_url.return_value = test_concept_simple_view.thumbnail_url
        self.handler.receive(CreateConcept(
            auth_token=test_auth_token,
            **test_concept_payload.dict()
        ))
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_201_CREATED
        assert self.handler.result.body == test_concept_simple_view
        mock_s3_url.assert_called_once_with(f'thumbnails/{test_concept_payload.author}/{test_concept_payload.title}')
        mock_query_result.one.assert_called_once()
        mock_query.assert_called_once()
        mock_auth_check.assert_called_once_with(test_auth_token)

    @patch.object(AuthorizationRequired, '_check_if_authorized')
    @patch.object(S3Crud, 'share_item')
    def test_duplicate_concept_creation(
        self,
        mock_s3_url,
        mock_auth_check,
        mock_query_result,
        mock_query,
        test_auth_token,
        test_concept_payload,
        test_concept_simple_view
    ):
        mock_query.side_effect = IntegrityError("doing", "a", "test")
        self.handler.receive(CreateConcept(
            auth_token=test_auth_token,
            **test_concept_payload.dict()
        ))
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_403_FORBIDDEN
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg=f'{test_concept_payload.author}/{test_concept_payload.title} is not available'
                )

    @pytest.mark.parametrize("err_type, err_msg", [
        (NotAuthorizedError, 'Invalid token presented'),
        (NotAuthorizedError, 'Unable to verify token ownership')
        ])
    @patch.object(AuthorizationRequired, '_check_if_authorized')
    @patch.object(S3Crud, 'share_item')
    def test_unauthorized_concept_creation(
        self,
        mock_s3_url,
        mock_auth_check,
        mock_query_result,
        mock_query,
        test_auth_token,
        test_concept_payload,
        test_concept_simple_view,
        err_type,
        err_msg
    ):
        mock_auth_check.side_effect = err_type(err_msg)
        self.handler.receive(CreateConcept(
            auth_token=test_auth_token,
            **test_concept_payload.dict()
        ))
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_401_UNAUTHORIZED
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg=err_msg
                )

    @patch.object(
            ConceptCreationHandler,
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
            test_concept_payload,
            test_auth_token
            ):
        self.handler.receive(CreateConcept(
            auth_token=test_auth_token,
            **test_concept_payload.dict()
        ))
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestConceptLinkingHandler:

    def setup_method(self):
        self.handler = ConceptLinkingHandler()
        self.handler.use_service(RegisteredService.CONCEPTS_DS)

    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_successful_linking_request(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_auth_token,
            test_linking_request
            ):
        mock_query_results.one.return_value = test_linking_request
        self.handler.receive(EstablishLink(
            auth_token=test_auth_token,
            **test_linking_request.dict()
        ))
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_201_CREATED
        assert self.handler.result.body == test_linking_request

    @pytest.mark.parametrize("err_type, err_cause, err_msg", [
        (IntegrityError, "not present in table", "Both concepts must exist to link them"),
        (IntegrityError, "already exists", "A link already exists between testuser/sample-idea and anotheruser/derived-idea")
        ])
    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_unsuccessful_linking_request(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_auth_token,
            test_linking_request,
            err_type,
            err_cause,
            err_msg
            ):
        mock_query_results.one.side_effect = err_type(err_cause, "", "")
        self.handler.receive(EstablishLink(
            auth_token=test_auth_token,
            **test_linking_request.dict()
        ))
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_403_FORBIDDEN
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg=err_msg
                )

    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_unauthorized_linking_request(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_auth_token,
            test_linking_request
            ):
        mock_auth_check.side_effect = NotAuthorizedError('Invalid token presented.')
        self.handler.receive(EstablishLink(
            auth_token=test_auth_token,
            **test_linking_request.dict()
            ))
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_401_UNAUTHORIZED
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Invalid token presented.'
                )

    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_self_referential_links_not_allowed(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_auth_token,
            test_linking_request
            ):
        test_linking_request.descendant = test_linking_request.ancestor
        self.handler.receive(EstablishLink(
            auth_token=test_auth_token,
            **test_linking_request.dict()
            ))
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_403_FORBIDDEN
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Self referential links not allowed'
                )

    @patch.object(
            ConceptLinkingHandler,
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
            test_auth_token,
            test_linking_request
            ):
        self.handler.receive(EstablishLink(
            auth_token=test_auth_token,
            **test_linking_request.dict()
            ))
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )

    @pytest.mark.xfail(raises=IntegrityError)
    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_a_really_weird_be_error(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_auth_token,
            test_linking_request
            ):
        mock_query_results.one.side_effect = IntegrityError("Some other integrity violation", "", "")
        self.handler.receive(EstablishLink(
            auth_token=test_auth_token,
            **test_linking_request.dict()
            ))


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestStartFollowingHandler:

    def setup_method(self):
        self.handler = StartFollowingAccountHandler()
        self.handler.use_service(RegisteredService.ENGAGE_DS)

    @patch.object(AuthorizationRequired, "_check_if_authorized")
    def test_successful_start_following_user(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_follow_request
            ):
        mock_query_results.one.return_value = AccountFollowingRecord(
                follower=test_follow_request.follower,
                followee=test_follow_request.followee
                )
        self.handler.receive(test_follow_request)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_201_CREATED
        assert self.handler.result.body == EndpointInformationalMessage(
                msg=f'{test_follow_request.follower} is now following {test_follow_request.followee}'
                )

    @pytest.mark.parametrize("err_type, err_cause, err_msg", [
        (IntegrityError, "not present in table", "Both accounts must exist to follow or be followed"),
        (IntegrityError, "already exists", "A following exists between user-a and user-b")
        ])
    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_invalid_follow_request(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_follow_request,
            err_type,
            err_cause,
            err_msg
            ):
        mock_query_results.one.side_effect = err_type(err_cause, "", "")
        self.handler.receive(test_follow_request)
        self.handler.status == EndpointHandlerStatus.ERROR
        self.handler.result.code == status.HTTP_403_FORBIDDEN
        self.handler.result.body == EndpointErrorMessage(
                err_msg=err_msg
                )

    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_attempt_to_follow_self(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_follow_request
            ):
        test_follow_request.followee = test_follow_request.follower
        self.handler.receive(test_follow_request)
        self.handler.status == EndpointHandlerStatus.ERROR
        self.handler.result.code == status.HTTP_403_FORBIDDEN
        self.handler.result.body == EndpointErrorMessage(
                err_msg="Cannot follow yourself. You'll need to make real connections"
                )

    @pytest.mark.parametrize("err_type, err_msg", [
        (NotAuthorizedError, 'Invalid token presented'),
        (NotAuthorizedError, 'Unable to verify token ownership')
        ])
    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_unauthorized_follow_request(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_follow_request,
            err_type,
            err_msg
            ):
        mock_auth_check.side_effect = err_type(err_msg)
        self.handler.receive(test_follow_request)
        self.handler.status == EndpointHandlerStatus.ERROR
        self.handler.result.code == status.HTTP_401_UNAUTHORIZED
        self.handler.result.body == EndpointErrorMessage(
                err_msg=err_msg
                )

    @patch.object(
            StartFollowingAccountHandler,
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
            test_follow_request
            ):
        self.handler.receive(test_follow_request)
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )

    @pytest.mark.xfail(raises=IntegrityError)
    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_a_really_weird_be_error(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_follow_request
            ):
        mock_query_results.one.side_effect = IntegrityError("Some other integrity violation", "", "")
        self.handler.receive(test_follow_request)


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestStartLikingHandler:

    def setup_method(self):
        self.handler = StartLikingConceptHandler()
        self.handler.use_service(RegisteredService.ENGAGE_DS)

    @patch.object(AuthorizationRequired, "_check_if_authorized")
    def test_successful_start_liking_concept(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_like_request
            ):
        mock_query_results.one.return_value = Likes(
                display_name=test_like_request.user_liking,
                concept_id=test_like_request.concept_liked
                )
        self.handler.receive(test_like_request)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_201_CREATED
        assert self.handler.result.body == EndpointInformationalMessage(
                msg=f'{test_like_request.user_liking} now likes the concept of {test_like_request.concept_liked}'
                )

    @pytest.mark.parametrize("err_type, err_cause, err_msg", [
        (IntegrityError, "not present in table", "Both accounnt concept must exist"),
        (IntegrityError, "already exists", "A liking exists between someuser and testuser/sample-idea")
        ])
    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_invalid_like_request(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_like_request,
            err_type,
            err_cause,
            err_msg
            ):
        mock_query_results.one.side_effect = err_type(err_cause, "", "")
        self.handler.receive(test_like_request)
        self.handler.status == EndpointHandlerStatus.ERROR
        self.handler.result.code == status.HTTP_403_FORBIDDEN
        self.handler.result.body == EndpointErrorMessage(
                err_msg=err_msg
                )

    @pytest.mark.parametrize("err_type, err_msg", [
        (NotAuthorizedError, 'Invalid token presented'),
        (NotAuthorizedError, 'Unable to verify token ownership')
        ])
    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_unauthorized_like_request(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_like_request,
            err_type,
            err_msg
            ):
        mock_auth_check.side_effect = err_type(err_msg)
        self.handler.receive(test_like_request)
        self.handler.status == EndpointHandlerStatus.ERROR
        self.handler.result.code == status.HTTP_401_UNAUTHORIZED
        self.handler.result.body == EndpointErrorMessage(
                err_msg=err_msg
                )

    @patch.object(
            StartLikingConceptHandler,
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
            test_like_request
            ):
        self.handler.receive(test_like_request)
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )

    @pytest.mark.xfail(raises=IntegrityError)
    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_a_really_weird_be_error(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_like_request
            ):
        mock_query_results.one.side_effect = IntegrityError("Some other integrity violation", "", "")
        self.handler.receive(test_like_request)


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestCommentCreationHandler:

    def setup_method(self):
        self.handler = CommentCreationHandler()
        self.handler.use_service(RegisteredService.ENGAGE_DS)

    @patch.object(AuthorizationRequired, "_check_if_authorized")
    def test_successful_thread_creation(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_start_new_thread
            ):
        self.handler.receive(test_start_new_thread)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_201_CREATED
        assert self.handler.result.body == EndpointInformationalMessage(
                msg='Comment created successfully'
                )

    @patch.object(AuthorizationRequired, "_check_if_authorized")
    def test_successful_thread_contribution(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_responsd_in_thread
            ):
        self.handler.receive(test_responsd_in_thread)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_201_CREATED
        assert self.handler.result.body == EndpointInformationalMessage(
                msg='Comment created successfully'
                )

    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_invalid_comment_create(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_start_new_thread
            ):
        mock_query_results.one.side_effect = IntegrityError('not present in table', '', '')
        self.handler.receive(test_start_new_thread)
        self.handler.status == EndpointHandlerStatus.ERROR
        self.handler.result.code == status.HTTP_403_FORBIDDEN
        self.handler.result.body == EndpointErrorMessage(
                err_msg="Both the concept and author must exist to comment. "
                        "If responding to another comment, it must exist also."
                )

    @pytest.mark.parametrize("err_type, err_msg", [
        (NotAuthorizedError, 'Invalid token presented'),
        (NotAuthorizedError, 'Unable to verify token ownership')
        ])
    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_unauthorized_like_request(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_start_new_thread,
            err_type,
            err_msg
            ):
        mock_auth_check.side_effect = err_type(err_msg)
        self.handler.receive(test_start_new_thread)
        self.handler.status == EndpointHandlerStatus.ERROR
        self.handler.result.code == status.HTTP_401_UNAUTHORIZED
        self.handler.result.body == EndpointErrorMessage(
                err_msg=err_msg
                )

    @patch.object(
            CommentCreationHandler,
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
            test_start_new_thread
            ):
        self.handler.receive(test_start_new_thread)
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )

    @pytest.mark.xfail(raises=IntegrityError)
    @patch.object(AuthorizationRequired, '_check_if_authorized')
    def test_a_really_weird_be_error(
            self,
            mock_auth_check,
            mock_query_results,
            mock_query,
            test_start_new_thread
            ):
        mock_query_results.one.side_effect = IntegrityError("Some other integrity violation", "", "")
        self.handler.receive(test_start_new_thread)
