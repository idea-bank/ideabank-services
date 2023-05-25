"""Tests for api artifact models"""

from itertools import permutations

import pytest

from pydantic import ValidationError

from ideabank_webapi.models import (
        CredentialSet,
        AuthorizationToken,
        ProfileView
        )


def test_valid_credential_set():
    payload = {
            'display_name': 'username',
            'password': 'password1'
            }
    cred_set = CredentialSet(**payload)
    assert cred_set.display_name == 'username'
    assert cred_set.password == 'password1'


@pytest.mark.parametrize("username, password", [
    ("user", "s33kret"),
    ("me", "password1")
    ])
def test_invalid_credential_set(username, password):
    payload = {
            'display_name': username,
            'password': password
            }
    with pytest.raises(ValidationError):
        CredentialSet(**payload)
