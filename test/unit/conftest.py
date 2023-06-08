"""Pytest configuration"""

import pytest
import random
import string
import faker

from ideabank_webapi.models import AuthorizationToken


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
