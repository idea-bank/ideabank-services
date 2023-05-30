"""Tests for creator handlers"""

import pytest
from unittest.mock import patch
from ideabank_webapi.handlers import EndpointHandlerStatus
from ideabank_webapi.handlers.creators import (
        AccountCreationHandler,
        ConceptCreationHandler,
        ConceptLinkingHandler
        )
from ideabank_webapi.handlers.preprocessors import AuthorizationRequired
from ideabank_webapi.services import (
        RegisteredService,
        AccountsDataService,
        QueryService,
        ConceptsDataService
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
        ConceptLinkRecord
)
from ideabank_webapi.exceptions import BaseIdeaBankAPIException, NotAuthorizedError

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


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
@patch.object(QueryService, 'exec_next')
@patch.object(QueryService, 'results')
class TestAccountCreationHandler:

    def setup_method(self):
        self.handler = AccountCreationHandler()
        self.handler.use_service(RegisteredService.ACCOUNTS_DS, AccountsDataService())

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
        self.handler.use_service(RegisteredService.CONCEPTS_DS, ConceptsDataService())

    @patch.object(AuthorizationRequired, '_check_if_authorized')
    @patch.object(ConceptsDataService, 'share_item')
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
    @patch.object(ConceptsDataService, 'share_item')
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
    @patch.object(ConceptsDataService, 'share_item')
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
        self.handler.use_service(RegisteredService.CONCEPTS_DS, ConceptsDataService())

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
