"""Pytest configuration"""

import pytest
import random
import string
import faker

from ideabank_webapi.models import AuthorizationToken, ConceptSimpleView, CredentialSet


@pytest.fixture
def fake_jwt(scope='session'):
    return '.'.join(
            [
                ''.join(
                    random.choice(string.ascii_letters + string.digits)
                    for _ in range(random.randint(18, 72))
                    )
                for _ in range(3)
                ]
            )


@pytest.fixture
def test_auth_token(fake_jwt, faker):
    return AuthorizationToken(
            token=fake_jwt,
            presenter=faker.user_name()
            )


@pytest.fixture
def test_concept_simple_view(faker):
    fake_username = faker.user_name()
    fake_title = faker.domain_word()
    return ConceptSimpleView(
            identifier=f'{fake_username}/{fake_title}',
            thumbnail_url=f'http://example.com/thumbnails/{fake_username}/{fake_title}'
            )


@pytest.fixture
def test_creds_set(faker):
    return CredentialSet(
            display_name=faker.user_name(),
            password='supersecretpassword'
            )


