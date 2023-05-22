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
            'display_name': 'dXNlcm5hbWU=',
            'password': 'cGFzc3dvcmQ='
            }
    cred_set = CredentialSet(**payload)
    assert cred_set.display_name == 'username'
    assert cred_set.password == 'password'


def test_invalid_credential_set():
    payload = {
            'display_name': 'notadisplayname',
            'password': 'notapassword'
            }
    with pytest.raises(ValidationError):
        CredentialSet(**payload)


@pytest.mark.parametrize("display_name, password", permutations(
    [
        'YWJj',
        'YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWE=',
    ],
    2)
                         )
def test_misformatted_credential_set(display_name, password):
    payload = {
            'display_name': display_name,
            'password': password
            }
    with pytest.raises(ValidationError):
        CredentialSet(**payload)
