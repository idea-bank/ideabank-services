"""Tests for api artifact models"""

import datetime

import pytest
from freezegun import freeze_time
from pydantic import ValidationError

from ideabank_webapi.models import (
        CredentialSet,
        AccountRecord,
        ConceptSearchQuery
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
@pytest.mark.xfail(raises=ValidationError)
def test_invalid_account_record(username, hash, salt):
    AccountRecord(
            display_name=username,
            password_hash=hash,
            salt_value=salt
            )


@freeze_time("2023-01-16 18:30:11")
def test_default_date_range_in_search_params():
    search_params = ConceptSearchQuery(
            title='atitle',
            author='anauthor'
            )
    assert search_params.title == 'atitle'
    assert search_params.author == 'anauthor'
    assert search_params.not_before == datetime.datetime.fromtimestamp(0, datetime.timezone.utc)
    assert search_params.not_after == datetime.datetime.now(datetime.timezone.utc)
    assert search_params.fuzzy is False


@freeze_time("2023-01-16 18:30:11")
def test_non_default_date_range_in_search_params():
    search_params = ConceptSearchQuery(
            title='atitle',
            author='anauthor',
            not_before=datetime.datetime.utcnow() - datetime.timedelta(days=4),
            not_after=datetime.datetime.utcnow() - datetime.timedelta(days=2)
            )
    assert search_params.title == 'atitle'
    assert search_params.author == 'anauthor'
    assert search_params.not_before == datetime.datetime.utcnow() - datetime.timedelta(days=4)
    assert search_params.not_after == datetime.datetime.utcnow() - datetime.timedelta(days=2)
    assert search_params.fuzzy is False
