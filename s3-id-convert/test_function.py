"""
    :module_name: test_function
    :module_summary: tests for the function implementation
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

# pylint: skip-file

import unittest
from unittest.mock import patch

from ideabank_datalink.toolkit.blob_wrapper import BlobWrapper
from ideabank_datalink.exceptions import DataLinkBlobShareFailure
import function


class QueryParamSets:
    # Real requests would URLEncode these
    VALID = {
            function.BUCKET_PARAM_NAME: 'test-bucket',
            function.OBJECT_KEY_PARAM_NAME: 'test/key/path'
            }
    MISS_ONE = {
            function.OBJECT_KEY_PARAM_NAME: 'test/key/path'
            }
    MISS_BOTH = {

            }
    MISS_ONE_AND_ONE_UNEXPECTED = {
            function.BUCKET_PARAM_NAME: 'test-bucket',
            'key1': 'value1'
            }
    MISS_BOTH_AND_BOTH_UNEXPECTED = {
            'key1': 'value1',
            'key2': 'value2'
            }
    VALID_BUT_HAS_EXTRA = {
            function.BUCKET_PARAM_NAME: 'test-bucket',
            function.OBJECT_KEY_PARAM_NAME: 'test/key/path',
            'key3': 'value3'
            }


class TestWrapperCreationFromQueryParameters(unittest.TestCase):

    def test_textbook_example_of_query_param_set(self):
        blob = function.make_blob_wrapper_from_query_parameters(QueryParamSets.VALID)
        self.assertIsNotNone(blob)
        self.assertIsInstance(blob, BlobWrapper)

    def test_valid_but_extra_paramters(self):
        blob = function.make_blob_wrapper_from_query_parameters(QueryParamSets.VALID_BUT_HAS_EXTRA)
        self.assertIsNotNone(blob)
        self.assertIsInstance(blob, BlobWrapper)

    def test_exception_thrown_when_one_parameter_missing(self):
        with self.assertRaises(function.MissingQueryStringParameterError):
            function.make_blob_wrapper_from_query_parameters(QueryParamSets.MISS_ONE)

    def test_expection_thrown_when_parameter_set_is_empty(self):
        with self.assertRaises(function.MissingQueryStringParameterError):
            function.make_blob_wrapper_from_query_parameters(QueryParamSets.MISS_BOTH)

    def test_exception_thrown_when_expected_parameter_is_substituted(self):
        for qs in [QueryParamSets.MISS_ONE_AND_ONE_UNEXPECTED, QueryParamSets.MISS_BOTH_AND_BOTH_UNEXPECTED]:
            with self.assertRaises(function.MissingQueryStringParameterError):
                function.make_blob_wrapper_from_query_parameters(qs)


class TestHandler(unittest.TestCase):

    @patch.object(BlobWrapper, 'share', return_value='https://s3.aws.com/share-for-test-key-path-in-test-bucket')
    def test_successful_service_execution(self, mocks3):
        response = function.handler({
            'queryStringParameters': QueryParamSets.VALID
            }, {})
        self.assertEqual(response['statusCode'], 200)
        mocks3.assert_called_once()

    @patch.object(BlobWrapper, 'share', side_effect=DataLinkBlobShareFailure)
    def test_timeout_response(self, mocks3):
        response = function.handler({
            'queryStringParameters': QueryParamSets.VALID
            }, {})
        self.assertEqual(response['statusCode'], 504)
        mocks3.assert_called_once()

    def test_bad_request_response(self):
        response = function.handler({
            'queryStringParameters': QueryParamSets.MISS_ONE
            }, {})
        self.assertEqual(response['statusCode'], 400)


if __name__ == '__main__':
    unittest.main()
