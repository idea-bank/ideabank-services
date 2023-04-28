"""
    :module_name: test_function
    :module_summary: tests for the function implementation
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

# pylint: skip-file

import json
import unittest
import secrets
import jwt
from unittest.mock import patch

from ideabank_datalink.model.account import IdeaBankAccount
from ideabank_datalink.toolkit.accounts_table import IdeaBankAccountsTable
from ideabank_datalink.exceptions import DataLinkTableScanFailure
import function


class AuthorizationPayloads:
    NEW_TOKEN_REQUEST = {
        function.PAYLOAD_AUTHENTICATE_KEY: function.AuthKeyType.USERPASSPAIR.value,
        function.PAYLOAD_CREDENTIALS_KEY: "dXNlcm5hbWU6cGFzc3dvcmQ="
        }
    VERIFY_TOKEN_REQUEST = {
        function.PAYLOAD_AUTHENTICATE_KEY: function.AuthKeyType.WEBTOKEN.value,
        function.PAYLOAD_CREDENTIALS_KEY: {
            "username": "user",
            "jwt": "testtoken"
            }
        }


class TestExtractBodyFunction(unittest.TestCase):

    def test_extract_new_token_request(self):
        data = function.extract_from_body(json.dumps(AuthorizationPayloads.NEW_TOKEN_REQUEST))
        self.assertEqual(data[0], function.AuthKeyType.USERPASSPAIR.value)
        self.assertEqual(data[1], AuthorizationPayloads.NEW_TOKEN_REQUEST[function.PAYLOAD_CREDENTIALS_KEY])

    def test_extract_verify_token_request(self):
        data = function.extract_from_body(json.dumps(AuthorizationPayloads.VERIFY_TOKEN_REQUEST))
        self.assertEqual(data[0], function.AuthKeyType.WEBTOKEN.value)
        self.assertEqual(data[1], AuthorizationPayloads.VERIFY_TOKEN_REQUEST[function.PAYLOAD_CREDENTIALS_KEY])


class TestValidateCredentials(unittest.TestCase):

    @patch.object(
            IdeaBankAccountsTable,
            'get_from_table',
            **{
                'return_value': {
                    IdeaBankAccount.AUTHORIZER_ATTRIBUTE_KEY: {
                        'Password': 's3kr3t',
                        'Salt': 'salty'
                        }
                    }
                }
            )
    @patch('secrets.compare_digest', return_value=True)
    @patch('jwt.encode', return_value='testtoken')
    def test_password_successfully_validated(self, mockjwt, mockcmp, mockdb):
        self.assertEqual(
            'testtoken',
            function.validate_credentials(
                AuthorizationPayloads.NEW_TOKEN_REQUEST[function.PAYLOAD_CREDENTIALS_KEY]
                )
        )
        mockjwt.assert_called_once()
        mockcmp.assert_called_once()
        mockdb.assert_called_once_with({IdeaBankAccount.PARTITION_KEY: 'username'})

    @patch.object(
            IdeaBankAccountsTable,
            'get_from_table',
            **{
                'return_value': {
                    IdeaBankAccount.AUTHORIZER_ATTRIBUTE_KEY: {
                        'Password': 's3kr3t',
                        'Salt': 'salty'
                        }
                    }
                }
            )
    @patch('secrets.compare_digest', return_value=False)
    def test_password_not_validated_because_it_is_wrong(self, mockcmp, mockdb):
        with self.assertRaises(function.NotAuthorizedError):
            function.validate_credentials(
                    AuthorizationPayloads.NEW_TOKEN_REQUEST[function.PAYLOAD_CREDENTIALS_KEY]
                    )
        mockcmp.assert_called_once()
        mockdb.assert_called_once_with({IdeaBankAccount.PARTITION_KEY: 'username'})

    @patch.object(
            IdeaBankAccountsTable,
            'get_from_table',
            **{
                'side_effect': DataLinkTableScanFailure
                }
            )
    def test_password_not_validated_because_account_not_found(self, mockdb):
        with self.assertRaises(function.NotAuthorizedError):
            function.validate_credentials(
                    AuthorizationPayloads.NEW_TOKEN_REQUEST[function.PAYLOAD_CREDENTIALS_KEY]
                    )
        mockdb.assert_called_once_with({IdeaBankAccount.PARTITION_KEY: 'username'})

    def test_password_not_validated_because_it_is_malformed(self):
        with self.assertRaises(function.NotAuthorizedError):
            function.validate_credentials('username%password')


class TestVerifyClaims(unittest.TestCase):

    def test_claims_not_verified_because_no_token_is_present(self):
        self.assertFalse(
            function.validate_claims(
                    {
                        'fakejwt': 'faketoken',
                        'username': 'user'
                        }
                    )
            )

    @patch('jwt.decode', side_effect=jwt.exceptions.ExpiredSignatureError)
    def test_claims_not_verified_because_token_is_expired(self, mockjwt):
        self.assertFalse(
                function.validate_claims(
                    AuthorizationPayloads.VERIFY_TOKEN_REQUEST[function.PAYLOAD_CREDENTIALS_KEY]
                    )
                )
        mockjwt.assert_called_once()

    @patch('jwt.decode', side_effect=jwt.exceptions.DecodeError)
    def test_claims_not_verified_because_token_is_malformed(self, mockjwt):
        self.assertFalse(
                function.validate_claims(
                    AuthorizationPayloads.VERIFY_TOKEN_REQUEST[function.PAYLOAD_CREDENTIALS_KEY]
                    )
                )
        mockjwt.assert_called_once()

    @patch('jwt.decode', return_value={'username': 'notuser'})
    def test_claims_not_verified_because_token_owner_is_wrong(self, mockjwt):
        self.assertFalse(
                function.validate_claims(
                    AuthorizationPayloads.VERIFY_TOKEN_REQUEST[function.PAYLOAD_CREDENTIALS_KEY]
                    )
                )
        mockjwt.assert_called_once()

    @patch('jwt.decode', return_value={'username': 'user'})
    def test_claims_verified_because_token_is_ok(self, mockjwt):
        self.assertTrue(
                function.validate_claims(
                    AuthorizationPayloads.VERIFY_TOKEN_REQUEST[function.PAYLOAD_CREDENTIALS_KEY]
                    )
                )
        mockjwt.assert_called_once()


class TestHandler(unittest.TestCase):
    @patch.object(
            IdeaBankAccountsTable,
            'get_from_table',
            **{
                'return_value': {
                    IdeaBankAccount.AUTHORIZER_ATTRIBUTE_KEY: {
                        'Password': 's3kr3t',
                        'Salt': 'salty'
                        }
                    }
                }
            )
    @patch('secrets.compare_digest', return_value=True)
    @patch('jwt.encode', return_value='testtoken')
    def test_ok_response_with_valid_username_password_combo(
            self,
            mockjwt,
            mockcmp,
            mockdb
            ):
        response = function.handler(
                {
                    'body': json.dumps(AuthorizationPayloads.NEW_TOKEN_REQUEST)},
                {}
            )
        assert response['statusCode'] == 200

    @patch('secrets.compare_digest', return_value=True)
    @patch('jwt.decode', return_value={'username': 'user'})
    def test_ok_response_with_verifiable_claims(self, mockjwt, mockcmp):
        response = function.handler(
                {
                    'body': json.dumps(AuthorizationPayloads.VERIFY_TOKEN_REQUEST)
                    },
                {}
                )
        assert response['statusCode'] == 200

    @patch('function.validate_credentials', side_effect=function.NotAuthorizedError)
    def test_unauthorized_response_with_invalid_username_password_combo(self, mockcreds):
        response = function.handler(
                {
                    'body': json.dumps(AuthorizationPayloads.NEW_TOKEN_REQUEST)
                    },
                {}
                )
        assert response['statusCode'] == 401

    @patch('function.validate_claims', side_effect=function.NotAuthorizedError)
    def test_unauthorized_response_with_invalide_token(self, mockcreds):
        response = function.handler(
                {
                    'body': json.dumps(AuthorizationPayloads.VERIFY_TOKEN_REQUEST)
                    },
                {}
                )
        assert response['statusCode'] == 401

    def test_unauthorized_response_with_invalid_key_type(self):
        response = function.handler(
                {
                    'body': json.dumps(
                        {
                            function.PAYLOAD_AUTHENTICATE_KEY: 'what key',
                            function.PAYLOAD_CREDENTIALS_KEY: 'lol'
                            }
                        )
                    },
                {}
                )
        assert response['statusCode'] == 401

    @patch('function.validate_credentials', side_effect=DataLinkTableScanFailure)
    def test_timeout_response_when_validated_account_credentials(self, mockdb):
        response = function.handler(
                {
                    'body': json.dumps(AuthorizationPayloads.NEW_TOKEN_REQUEST)
                    },
                {}
                )
        assert response['statusCode'] == 503


if __name__ == '__main__':
    unittest.main()
