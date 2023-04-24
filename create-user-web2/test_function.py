"""
    :module_name: test_function
    :module_summary: tests for the create user web2 service
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

# pylint: skip-file

import json
import unittest
from unittest.mock import patch

from ideabank_datalink.toolkit.accounts_table import IdeaBankAccountsTable
from botocore.exceptions import ClientError

from function import handler, extract_from_body, username_taken


class PayloadTestData:
    EVENT_OK = {
        'body': '{\n\t"displayName": "somethingcatchy",' +
                '\n\t"credentials": ' +
                '"c29tZXRoaW5nQHRoaXNwbGFjZS5uZXQ6Y3JlYXRpdmVseXNlcmN1cmU="\n}'
    }
    EVENT_TOO_SHORT = {
        'body': '{\n\t"displayName": 5,\n\t"credentials": "d2hhdCBhcmUgdGhvc2U/"\n}'
        }
    EVENT_NOT_VALID_JSON = {
            'body': '{\n\t"displayName": "somethingcatchy", ["what", "is", "this?"]}'
            }
    EVENT_NOT_COMPLETE = {
            'body': '{\n\t"displayName": "somethingcatchy"}'
            }


class TestPayloadExtraction(unittest.TestCase):
    """Tests for payload extraction"""

    def test_successful_data_extraction(self):
        payload = extract_from_body(PayloadTestData.EVENT_OK['body'])
        self.assertEqual(3, len(payload))
        self.assertTupleEqual(
                (
                    "somethingcatchy",
                    "something@thisplace.net",
                    "creativelysercure"
                    ),
                payload
                )

    def test_unsuccessfull_extraction_because_of_inappropriate_length(self):
        with self.assertRaises(IndexError):
            extract_from_body(PayloadTestData.EVENT_TOO_SHORT['body'])

    def test_unsuccesfull_extraction_because_format_is_not_valid(self):
        with self.assertRaises(json.JSONDecodeError):
            extract_from_body(PayloadTestData.EVENT_NOT_VALID_JSON['body'])

    def test_unsuccesfull_extraction_because_of_incomplete_payload(self):
        with self.assertRaises(KeyError):
            extract_from_body(PayloadTestData.EVENT_NOT_COMPLETE['body'])


class TestHandler(unittest.TestCase):
    """Tests for lambda handler"""

    @patch.object(IdeaBankAccountsTable, 'table')
    @patch('function.username_taken', return_value=False)
    def test_successful_user_creation(self, mockduplicates, mockdb):
        response = handler(PayloadTestData.EVENT_OK, {})
        self.assertEqual(response['statusCode'], 201)

    @patch.object(IdeaBankAccountsTable, 'table')
    def test_unsuccesfull_user_creation_because_of_bad_request_1(self, mockdb):
        response = handler(PayloadTestData.EVENT_TOO_SHORT, {})
        self.assertEqual(response['statusCode'], 400)

    @patch.object(IdeaBankAccountsTable, 'table')
    def test_unsuccesfull_user_creation_because_of_bad_request_2(self, mockdb):
        response = handler(PayloadTestData.EVENT_NOT_COMPLETE, {})
        self.assertEqual(response['statusCode'], 400)

    @patch.object(IdeaBankAccountsTable, 'table')
    def test_unsuccesfull_user_creation_because_of_bad_request_3(self, mockdb):
        response = handler(PayloadTestData.EVENT_NOT_VALID_JSON, {})
        self.assertEqual(response['statusCode'], 400)

    @patch.object(IdeaBankAccountsTable, 'table')
    @patch('function.username_taken', return_value=False)
    def test_unsuccesfull_user_creation_because_of_datalink_failure(
            self,
            mockduplicates,
            mockdb
            ):
        mockdb.put_item.side_effect = ClientError(
                {
                    'Error': {
                        'Code': 'test',
                        'Message': 'doing a test here'
                    }
                }, 'testing'
                                                  )
        response = handler(PayloadTestData.EVENT_OK, {})
        self.assertEqual(response['statusCode'], 503)

    @patch.object(IdeaBankAccountsTable, 'table')
    @patch('function.username_taken', return_value=True)
    def test_unsuccesfull_user_creation_because_of_duplicate_name(
            self,
            mockduplicates,
            mockdb
            ):
        response = handler(PayloadTestData.EVENT_OK, {})
        self.assertEqual(response['statusCode'], 503)  # TODO: Update with appropriate code


if __name__ == '__main__':
    unittest.main()
