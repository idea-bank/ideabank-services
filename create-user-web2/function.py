"""
    :module_name: function
    :module_summary: main function execution logic
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import os
import base64
import binascii
import json

from ideabank_datalink.model.users import IdeaBankUser, AuthKey
from ideabank_datalink.toolkit.users_table import IdeaBankUsersTable
from ideabank_datalink.exceptions import DataLinkTableInteractionException

LOGGER = logging.getLogger(__name__)

LOG_HANDLER = logging.StreamHandler()

if os.getenv('ENV') == 'prod':
    LOGGER.setLevel(logging.INFO)
    LOG_HANDLER.setLevel(logging.INFO)
else:
    LOGGER.setLevel(logging.DEBUG)
    LOG_HANDLER.setLevel(logging.DEBUG)

PAYLOAD_DISPLAY_NAME_KEY = 'displayName'
PAYLOAD_CREDENTIALS_KEY = 'credentials'


def extract_from_body(payload: str) -> (str, str, str):
    """Interpret the payload as a JSON document and extract required info
    Arguments:
        payload: [str] -- JSON document as a string to extract from
    Returns:
        user info: [tuple] -- contains username, email, and password
    Raises:
        json.JSONDecodeError -- if the payload cannot be decoded
        KeyError -- if the expected information is not found
        ValueError -- if credentials cannot be decoded
        binascii.Error -- if credentials cannot be decoded
        IndexError -- if credentials are not the appropriate length
    """
    LOGGER.info("Decoding the HTTP payload ... ")
    doc = json.loads(payload)
    LOGGER.info("HTTP payload decoded successfully")
    LOGGER.info("Extracting information from payload")
    display_name = doc[PAYLOAD_DISPLAY_NAME_KEY]
    credentials = base64.b64decode(doc[PAYLOAD_CREDENTIALS_KEY].encode('utf-8')).decode('utf-8')
    return (
            display_name,
            credentials.split(':', 1)[0],
            credentials.split(':', 1)[1]
            )


def handler(event, context):  # pylint:disable=unused-argument
    """
        Handler function for the create web2 user microservice
    """
    try:
        name, email, raw_pass = extract_from_body(event['body'])
        table = IdeaBankUsersTable()
        table.put_into_table(IdeaBankUser.new(
                **{
                    IdeaBankUser.DISPLAY_NAME_KEY: name,
                    AuthKey.NEW_RAW_USER_KEY: email,
                    AuthKey.NEW_RAW_PASS_KEY: raw_pass
                    }
                )
            )
        return user_creation_confirmation()
    except KeyError as err:
        LOGGER.error("Missing expected information: %s", str(err))
        return bad_request_response(str(err))
    except (json.JSONDecodeError, ValueError, binascii.Error, IndexError) as err:
        LOGGER.error("Could not interpret payload: %s", str(err))
        return bad_request_response(str(err))
    except DataLinkTableInteractionException as err:
        LOGGER.error("Could not interact with DynamoDB: %s", str(err))
        return bad_gateway_response(str(err))


def headers() -> dict:
    """
        Function that specifies response headers
        :returns: headers mapping
        :rtype: dict
    """
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST'
    }


def user_creation_confirmation():
    """
        Successful response
    """
    LOGGER.info('Service succeeded')
    return {
            'isBase64Encoded': False,
            'statusCode': 201,
            'headers': headers(),
            'body': json.dumps({
                'success': {
                    'message': 'CREATED NEW USER'
                    }
                })
            }


def bad_request_response(err_msg: str):
    """
        Bad request response
    """
    LOGGER.error('Service could not process request')
    return {
            'isBase64Encoded': False,
            'statusCode': 400,
            'headers': headers(),
            'body': json.dumps({
                'error': {
                    'message': err_msg
                    }
                })
            }


def bad_gateway_response(err_msg: str):
    """
        Timeout response
    """
    LOGGER.error('Service could not interact with DynamoDB')
    return {
            'isBase64Encoded': False,
            'statusCode': 503,
            'headers': headers(),
            'body': json.dumps({
                'error': {
                    'message': err_msg
                    }
                })
            }
