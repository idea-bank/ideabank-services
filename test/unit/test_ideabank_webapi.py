"""Tests for ideabank_webapi"""

import pytest
from unittest.mock import patch, PropertyMock
from fastapi import status
from fastapi.testclient import TestClient

from ideabank_webapi import app
from ideabank_webapi.handlers import BaseEndpointHandler, EndpointHandlerStatus
from ideabank_webapi.handlers.preprocessors import AuthorizationRequired
from ideabank_webapi.models import (
        EndpointResponse,
        EndpointInformationalMessage
        )


@pytest.fixture(scope='session')
def test_client():
    return TestClient(app)


test_response = EndpointResponse(
            code=status.HTTP_418_IM_A_TEAPOT,
            body=EndpointInformationalMessage(msg="I'm a teapot")
            )


@pytest.mark.parametrize("endpoint", ['/accounts/create', '/accounts/authenticate'])
@patch.object(BaseEndpointHandler, 'receive')
@patch.object(BaseEndpointHandler, 'result', new_callable=PropertyMock, return_value=test_response)
@patch.object(BaseEndpointHandler, 'status', new_callable=PropertyMock, return_value=EndpointHandlerStatus.COMPLETE)
def test_post_accounts_endpoints(
        mock_status,
        mock_result,
        mock_receive,
        endpoint,
        test_client,
        ):
    test_client.post(
            endpoint,
            json={
                'display_name': 'testuser',
                'password': 'supersecretpassword'
                }
            )


@patch.object(BaseEndpointHandler, 'receive')
@patch.object(BaseEndpointHandler, 'result', new_callable=PropertyMock, return_value=test_response)
@patch.object(BaseEndpointHandler, 'status', new_callable=PropertyMock, return_value=EndpointHandlerStatus.COMPLETE)
def test_get_accounts_endpoint(
        mock_status,
        mock_result,
        mock_receive,
        test_client
        ):
    test_client.get(
            '/accounts/testuser/profile'
            )


@patch.object(AuthorizationRequired, 'receive')
@patch.object(BaseEndpointHandler, 'result', new_callable=PropertyMock, return_value=test_response)
@patch.object(BaseEndpointHandler, 'status', new_callable=PropertyMock, return_value=EndpointHandlerStatus.COMPLETE)
def test_new_concept_endpoint(
        mock_status,
        mock_result,
        mock_receive,
        test_client,
        test_auth_token
        ):
    test_client.post(
        '/concepts',
        headers={'authorization': test_auth_token.token},
        json={
            'author': 'testuser',
            'title': 'sample-idea',
            'description': 'a really cool idea',
            'diagram': {}
            }
        )


@patch.object(AuthorizationRequired, 'receive')
@patch.object(BaseEndpointHandler, 'result', new_callable=PropertyMock, return_value=test_response)
@patch.object(BaseEndpointHandler, 'status', new_callable=PropertyMock, return_value=EndpointHandlerStatus.COMPLETE)
def test_new_link_endpoint(
        mock_status,
        mock_result,
        mock_receive,
        test_client,
        test_auth_token
        ):
    test_client.post(
            '/links',
            headers={'authorization': test_auth_token.token},
            json={
                'ancestor': 'testuser/a-previous-idea',
                'descendant': 'anotheruser/a-new-and-improved-idea'
                }
            )


@pytest.mark.parametrize("endpoint", [
    '/concepts/testuser/sample-idea',
    '/concepts?author=testuser&fuzzy=title-only',
    '/concepts/testuser/sample-idea/lineage',
    '/concepts/testuser/sample-idea/comments'
    ])
@patch.object(BaseEndpointHandler, 'receive')
@patch.object(BaseEndpointHandler, 'result', new_callable=PropertyMock, return_value=test_response)
@patch.object(BaseEndpointHandler, 'status', new_callable=PropertyMock, return_value=EndpointHandlerStatus.COMPLETE)
def test_get_concepts_endpoints(
        mock_status,
        mock_result,
        mock_receive,
        endpoint,
        test_client
        ):
    test_client.get(endpoint)


@patch.object(AuthorizationRequired, 'receive')
@patch.object(BaseEndpointHandler, 'result', new_callable=PropertyMock, return_value=test_response)
@patch.object(BaseEndpointHandler, 'status', new_callable=PropertyMock, return_value=EndpointHandlerStatus.COMPLETE)
def test_follow_cycle_endpoints(
        mock_status,
        mock_result,
        mock_receive,
        test_client,
        test_auth_token
        ):
    test_client.post(
            '/accounts/follow',
            headers={'authorization': test_auth_token.token},
            json={
                'follower': 'testuser',
                'followee': 'someuser'
                }
            )
    test_client.request(
            'delete',
            '/accounts/follow',
            headers={'authorization': test_auth_token.token},
            json={
                'follower': 'testuser',
                'followee': 'someuser'
                }
            )


@patch.object(BaseEndpointHandler, 'receive')
@patch.object(BaseEndpointHandler, 'result', new_callable=PropertyMock, return_value=test_response)
@patch.object(BaseEndpointHandler, 'status', new_callable=PropertyMock, return_value=EndpointHandlerStatus.COMPLETE)
def test_check_follow_status_endpoint(
        mock_status,
        mock_result,
        mock_receive,
        test_client
        ):
    test_client.get('accounts/testuser/follows/someuser')


@patch.object(AuthorizationRequired, 'receive')
@patch.object(BaseEndpointHandler, 'result', new_callable=PropertyMock, return_value=test_response)
@patch.object(BaseEndpointHandler, 'status', new_callable=PropertyMock, return_value=EndpointHandlerStatus.COMPLETE)
def test_like_cycle_endpoints(
        mock_status,
        mock_result,
        mock_receive,
        test_client,
        test_auth_token
        ):
    test_client.post(
            '/accounts/likes',
            headers={'authorization': test_auth_token.token},
            json={
                'user_liking': 'testuser',
                'concept_liked': 'someuser/cool-idea'
                }
            )
    test_client.request(
            'delete',
            '/accounts/likes',
            headers={'authorization': test_auth_token.token},
            json={
                'user_liking': 'testuser',
                'concept_liked': 'someuser/cool-idea'
                }
            )


@patch.object(BaseEndpointHandler, 'receive')
@patch.object(BaseEndpointHandler, 'result', new_callable=PropertyMock, return_value=test_response)
@patch.object(BaseEndpointHandler, 'status', new_callable=PropertyMock, return_value=EndpointHandlerStatus.COMPLETE)
def test_check_like_status_endpoint(
        mock_status,
        mock_result,
        mock_receive,
        test_client
        ):
    test_client.get('accounts/testuser/likes/someuser/cool-idea')


@patch.object(AuthorizationRequired, 'receive')
@patch.object(BaseEndpointHandler, 'result', new_callable=PropertyMock, return_value=test_response)
@patch.object(BaseEndpointHandler, 'status', new_callable=PropertyMock, return_value=EndpointHandlerStatus.COMPLETE)
def test_new_comment_endpoint(
        mock_status,
        mock_result,
        mock_receive,
        test_client,
        test_auth_token
        ):
    test_client.post(
        '/concepts/someuser/some-idea/comment',
        headers={'authorization': test_auth_token.token},
        json={
            'comment_author': 'testuser',
            'comment_text': 'I like this'
            }
        )


@patch.object(BaseEndpointHandler, 'receive')
@patch.object(BaseEndpointHandler, 'result', new_callable=PropertyMock, return_value=test_response)
@patch.object(BaseEndpointHandler, 'status', new_callable=PropertyMock, return_value=EndpointHandlerStatus.COMPLETE)
def test_get_comment_endpoint(
        mock_status,
        mock_result,
        mock_receive,
        test_client
        ):
    test_client.get('/concepts/someuser/cool-idea/comment')
