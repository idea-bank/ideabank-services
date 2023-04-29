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

from ideabank_datalink.model.account import IdeaBankAccount
from ideabank_datalink.toolkit.accounts_table import IdeaBankAccountsTable
from ideabank_datalink.exceptions import (
        DataLinkTableInteractionException,
        DataLinkTableScanFailure
        )

LOGGER = logging.getLogger(__name__)

LOG_HANDLER = logging.StreamHandler()

if os.getenv('ENV') == 'prod':
    LOGGER.setLevel(logging.INFO)
    LOG_HANDLER.setLevel(logging.INFO)
else:
    LOGGER.setLevel(logging.DEBUG)
    LOG_HANDLER.setLevel(logging.DEBUG)

PAYLOAD_NEW_ACCOUNT_KEY = 'NewAccount'


class DuplicateAccountError(Exception):
    """Exception raised when attempting to create a duplicate account"""


def extract_from_body(payload: str) -> (str, str):
    """Interpret the payload as a JSON document and extract required info
    Arguments:
        payload: [str] -- JSON document as a string to extract from
    Returns:
        user info: [tuple] -- contains username and password
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
    credentials = base64.b64decode(doc[PAYLOAD_NEW_ACCOUNT_KEY].encode('utf-8')).decode('utf-8')
    return (
            credentials.split(':', 1)[0],
            credentials.split(':', 1)[1]
            )


# Awaiting library enhancment before deprecating
def username_taken(table, user):
    """Checks if a username is available
    Arguments:
        table: table to Checks
        user: username requested
    Returns:
        True if username already in use
        False if username is available
    """
    LOGGER.info("Checking if `%s` is an available username", user.item_key)
    try:
        table.get_from_table(user.as_key())
        LOGGER.info(
                "`%s` has already been claimed. Refusing to create the account",
                user.item_key
                )
        return True
    except DataLinkTableScanFailure:
        LOGGER.info(
                "`%s` has not yet been claimed. Continuing with account creation",
                user.item_key
                )
        return False


def handler(event, context):  # pylint:disable=unused-argument
    """
        Handler function for the create web2 user microservice
    """
    try:
        username, raw_pass = extract_from_body(event['body'])
        table = IdeaBankAccountsTable()
        LOGGER.info("Creating new user account")
        user = IdeaBankAccount.create_new(
                **{
                    IdeaBankAccount.PARTITION_KEY: username,
                    IdeaBankAccount.AUTHORIZER_ATTRIBUTE_KEY: raw_pass
                    })
        LOGGER.debug(
                "New account created: %s",
                user.item_key,
                )
        LOGGER.info("Creating new record for account: %s", user.item_key)
        if username_taken(table, user):
            raise DuplicateAccountError(
                    f'Cannot create new account with `{user.item_key}`. It is already in use.'
                    )
        table.put_into_table(user)
        LOGGER.info("Successfully created new account record")
        return make_response(201, {'success': {'message': f'Acount created for `{username}`'}})
    except KeyError as err:
        LOGGER.error("Missing expected information: %s", str(err))
        return make_response(400, {'error': {'message': str(err)}})
    except (json.JSONDecodeError, ValueError, binascii.Error, IndexError) as err:
        LOGGER.error("Could not interpret payload: %s", str(err))
        return make_response(400, {'error': {'message': str(err)}})
    except DataLinkTableInteractionException as err:
        LOGGER.error("Could not interact with DynamoDB: %s", str(err))
        return make_response(503, {'error': {'message': str(err)}})
    except DuplicateAccountError as err:
        LOGGER.error("Cannot create account: %s", str(err))
        return make_response(401, {'error': {'message': str(err)}})


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


def make_response(status: int, body: dict) -> dict:
    """Creates a lambda proxy compliant response
    Arguments:
        status: [int] the HTTP status code of the response
        body: [dict] data structure to include in reponse body
    Returns:
        [dict] lambda proxy compliant response
    """
    LOGGER.info("Service reponse code: %d", status)
    return {
            'isBase64Encoded': False,
            'statusCode': status,
            'headers': headers(),
            'body': json.dumps(body)
            }
