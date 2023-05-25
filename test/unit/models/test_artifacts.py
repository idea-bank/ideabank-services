"""Tests for api artifact models"""

import pytest

from pydantic import ValidationError

from ideabank_webapi.models import (
        CredentialSet,
        AccountRecord
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


def test_valid_account_record():
    payload = {
            'display_name': 'username',
            'password_hash': 64 * 'a',
            'salt_value': 64 * 'b'
            }
    record = AccountRecord(**payload)
    assert record.display_name == 'username'
    assert record.password_hash == 64 * 'a'
    assert record.salt_value == 64 * 'b'


@pytest.mark.parametrize("username, hash, salt", [
    ('username1', 60 * 'a', 64 * 'b'),  # hash too short
    ('username2', 70 * 'a', 64 * 'b'),  # hash too long
    ('username3', 64 * 'a', 60 * 'b'),  # salt too short
    ('username4', 64 * 'a', 70 * 'b'),  # salt too long
    ('username5', 64 * 'z', 64 * 'b'),  # hash not hex
    ('username6', 64 * 'a', 64 * 'y')   # salt not hex
    ])
def test_invalid_account_record(username, hash, salt):
    with pytest.raises(ValidationError):
        AccountRecord(
                display_name=username,
                password_hash=hash,
                salt_value=salt
                )
