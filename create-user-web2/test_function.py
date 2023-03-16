"""
    :module_name: test_function
    :module_summary: tests for the create user web2 service
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

# pylint: skip-file

import unittest
from unittest.mock import patch

from botocore.exceptions import ClientError

from function import (InputDecoder, NewUser, Web2Key, IdeaBankUser,
                      handler,
                      MalformedDataException, MissingInformationException, UserCreationException)

class TestInputDecoder(unittest.TestCase):
    """Tests for input decoder"""
    def setUp(self):
        self._valid_body = '{\n\t"displayName": "somethingcatchy",' + \
                            '\n\t"credentials": '+ \
                            '"c29tZXRoaW5nQHRoaXNwbGFjZS5uZXQ6Y3JlYXRpdmVseXNlcmN1cmU="\n}'
        self._invalid_body = 'Definitely not a JSON object'
        self._false_body = '{\n\t"displayName": 5,\n\t"credentials":"what are those?"\n}'

    def test_body_can_be_interpreted_as_json(self):
        """check that body in json"""
        decoder = InputDecoder(self._valid_body)
        self.assertTrue(hasattr(decoder, '_input'))
        self.assertTrue(isinstance(decoder._input, dict))
        self.assertTrue(hasattr(decoder, '_display_name'))
        self.assertTrue(decoder._display_name is None)
        self.assertTrue(hasattr(decoder, '_credential_string'))
        self.assertTrue(decoder._credential_string is None)

    def test_invalid_body_raises_malformed_data_exception(self):
        """check body is not json is bad"""
        with self.assertRaises(MalformedDataException):
            InputDecoder(self._invalid_body)

    def test_data_extracts_required_keys(self):
        """check for required keys in body"""
        decoder = InputDecoder(self._valid_body).extract()
        self.assertEqual(decoder._display_name, decoder._input['displayName'])
        self.assertEqual(decoder._credential_string, decoder._input['credentials'])

    def test_data_extraction_fails_if_missing_display_name_key(self):
        """check for required keys in body"""
        decoder = InputDecoder(self._valid_body)
        decoder._input.pop('displayName')
        with self.assertRaises(MissingInformationException):
            decoder.extract()

    def test_data_extraction_fails_if_missing_credentials_key(self):
        """check fore required keys in body"""
        decoder = InputDecoder(self._valid_body)
        decoder._input.pop('credentials')
        with self.assertRaises(MissingInformationException):
            decoder.extract()

    def test_decode_returns_data_structure_containing_extracted_data(self):
        """check data extracted in expected form"""
        data = InputDecoder(self._valid_body).extract().decode()
        self.assertTrue(all(key in data for key in ['display_name', 'user_email', 'user_pass']))

    def test_cannot_decode_before_extract_is_called(self):
        """check extract happens before decode"""
        with self.assertRaises(MissingInformationException):
            InputDecoder(self._valid_body).decode()

    def test_cannot_decode_data_if_extracting_garbage_data(self):
        """check decode fails if extracting nonsense"""
        with self.assertRaises(MalformedDataException):
            InputDecoder(self._false_body).extract().decode()

class TestWeb2Key(unittest.TestCase):
    """Tests for web2 auth key"""
    def setUp(self):
        self._user = "username@domain.com"
        self._pass = "supersecretpassword"
        self._key = Web2Key(self._user, self._pass)

    def test_key_composed_of_three_parts(self):
        """check parts of key exists"""
        self.assertTrue(hasattr(self._key, 'email'))
        self.assertTrue(hasattr(self._key, 'pass_hash'))
        self.assertTrue(hasattr(self._key, 'salt'))

    def test_password_has_is_different_than_actual(self):
        """check password is not the hash"""
        self.assertFalse(self._key.pass_hash == self._pass)

class TestNewUser(unittest.TestCase):
    """Tests for new user class"""
    def setUp(self):
        self._keys = {'web2': Web2Key('username@domain.com', 'supersecretpassword')}
        self._user = NewUser('displayname', **self._keys)


    def test_new_user_composed_of_three_parts(self):
        """check parts of user exists"""
        self.assertTrue(hasattr(self._user, 'uuid'))
        self.assertTrue(hasattr(self._user, 'display_name'))
        self.assertTrue(hasattr(self._user, 'authkeys'))
        self.assertIsInstance(self._user.authkeys, dict)

class TestIdeaBankUser(unittest.TestCase):
    """Test for idea bank user table"""
    def setUp(self):
        self._keys = {'web2': Web2Key('username@domain.com', 'supersecretpassword')}
        self._user = NewUser('displayname', **self._keys)
        self._table = IdeaBankUser()

    def test_that_table_property_is_constant(self):
        """check table name is accurate"""
        self.assertEqual(self._table.table, "idea_bank_users_")

    @patch.object(IdeaBankUser, 'resource')
    def test_create_user_puts_new_item_in_database(self, mock_db_client):
        """check put item is called when user created"""
        self._table.create_user(self._user)
        mock_db_client.put_item.assert_called_once()

    @patch.object(IdeaBankUser, 'resource')
    def test_failure_to_create_user_raises_exception(self, mock_db_client):
        """check failure to put item is handled"""
        mock_db_client.put_item.side_effect=ClientError(
                {
                    'Error': {
                        'Code': 'test',
                        'Message': 'doing a test here'
                    }
                }, 'testing')
        with self.assertRaises(UserCreationException):
            self._table.create_user(self._user)

class TestHandler(unittest.TestCase):
    """Tests for lambda handler"""
    def setUp(self):
        self._event_ok = {
            'body': '{\n\t"displayName": "somethingcatchy",' + \
                    '\n\t"credentials": '+ \
                    '"c29tZXRoaW5nQHRoaXNwbGFjZS5uZXQ6Y3JlYXRpdmVseXNlcmN1cmU="\n}'
        }
        self._event_not_ok = {
            'body': '{\n\t"displayName": 5,\n\t"credentials":"what are those?"\n}'

        }

    @patch.object(IdeaBankUser, 'resource')
    def test_successful_execution(self, mock_db_client):
        """check ok status"""
        response = handler(self._event_ok, {})
        self.assertEqual(response['statusCode'], 201)

    def test_bad_request_execution(self):
        """check bad request status"""
        response = handler(self._event_not_ok, {})
        self.assertEqual(response['statusCode'], 400)

    @patch.object(IdeaBankUser, 'resource')
    def test_timeout_execution(self, mock_db_client):
        """check timeout status"""
        mock_db_client.put_item.side_effect=ClientError(
                {
                    'Error': {
                        'Code': 'test',
                        'Message': 'doing a test here'
                    }
                }, 'testing')
        response = handler(self._event_ok, {})
        self.assertEqual(response['statusCode'], 503)

if __name__ == '__main__':
    unittest.main()
