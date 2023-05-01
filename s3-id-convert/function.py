"""
    :module_name: function
    :module_summary: A service that creates presigned urls to objects in s3
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import os
import json

from ideabank_datalink.toolkit.blob_wrapper import BlobWrapper
from ideabank_datalink.exceptions import DataLinkBlobShareFailure


LOGGER = logging.getLogger(__name__)

LOG_HANDLER = logging.StreamHandler()

if os.getenv('ENV') == 'prod':
    LOGGER.setLevel(logging.INFO)
    LOG_HANDLER.setLevel(logging.INFO)
else:
    LOGGER.setLevel(logging.DEBUG)
    LOG_HANDLER.setLevel(logging.DEBUG)

BUCKET_PARAM_NAME = 'bucket'
OBJECT_KEY_PARAM_NAME = 'key'


class MissingQueryStringParameterError(Exception):
    """Exception raised when expected query parameter is missing"""


def make_blob_wrapper_from_query_parameters(params: dict) -> BlobWrapper:
    """Create a reference to a blob from the given query parameters
    Arguments:
        params: [dict] Query parameters included in the request
    Returns:
        [BlobWrapper] refering to the object specified in the parameters
    Raises:
        MissingQueryStringParameterError if expected parameter is missing.
        Extraneous parameters are ignored"""
    try:
        LOGGER.info("%d query parameters were sent with the request", len(params))
        return BlobWrapper(
            bucket_name=params[BUCKET_PARAM_NAME],
            key_path=params[OBJECT_KEY_PARAM_NAME]
            )
    except KeyError as err:
        LOGGER.error("Missing expected query parameter: %s", str(err))
        raise MissingQueryStringParameterError(
                f'Expected {str(err)} as a query parameter, but was not presented.'
                ) from err


def handler(event, context):  # pylint:disable=unused-argument
    """A service that generates share links to s3 objects"""
    try:
        blob_reference = make_blob_wrapper_from_query_parameters(event['queryStringParameters'])
        share_link = blob_reference.share()
        return make_response(
                status=200,
                body={'success': {'link': share_link}}
                )
    except MissingQueryStringParameterError as err:
        return make_response(
                status=400,
                body={'error': {'message': str(err)}}
                )
    except DataLinkBlobShareFailure as err:
        return make_response(
                status=504,
                body={'error': {'message': str(err)}}
                )


def headers() -> dict:
    """
        Function that specifies response headers
        :returns: headers mapping
        :rtype: dict
    """
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET'
    }


def make_response(status: int, body: dict) -> dict:
    """
        Makes a lambda proxy compliant response
        Arguments:
            status: [int] the HTTP code to put in this response
            body: [dict] the mapping representing the response
        Returns:
            [dict] lambda proxy compliant response
    """
    LOGGER.info("Service response of %d", status)
    return {
            'isBase64Encoded': False,
            'statusCode': status,
            'headers': headers(),
            'body': json.dumps(body)
            }
