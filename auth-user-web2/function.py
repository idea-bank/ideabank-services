"""
    :module_name: function
    :module_summary: A service that authenticates users with traditional web2 methods
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import os
import base64
import binascii
import json
import enum
import hashlib
import secrets
import datetime
import jwt

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

PAYLOAD_CREDENTIALS_KEY = 'Credentials'
PAYLOAD_AUTHENTICATE_KEY = 'AuthKeyType'


class NotAuthorizedError(Exception):
    """Raised when credentials fail to authenticate the user"""


class AuthKeyType(enum.Enum):
    """Valid Authentication Key Types"""
    USERPASSPAIR = 'Username+Password'
    WEBTOKEN = 'WebToken'


def extract_from_body(payload: str) -> (str, str):
    """Intrepret the payload as a JSON document and required info
    Arguments:
        payload: [str] -- JSON document as a string to extract from
    Retuns:
        auth info: [tuple] -- contains credentails and credentials type
    Raises:
        json.JSONDecodeError -- if the payload cannot be decoded
        KeyError -- if the expected information is not found
    """
    LOGGER.info("Decoding the HTTP payload ...")
    doc = json.loads(payload)
    LOGGER.info("HTTP payload decoded successfully")
    LOGGER.info("Extracting information from payload")
    return (doc[PAYLOAD_AUTHENTICATE_KEY], doc[PAYLOAD_CREDENTIALS_KEY])


def validate_credentials(credentials: str) -> str:
    """Check if the provided credentials are correct.
    Arguments:
        credentials: [str] the credentials to validate
    Returns:
        jwt: [str] for additional authentication needed
    Raises:
        NotAuthorizedError -- if credentials could not be validated
    """
    LOGGER.info("Decoding provided credentials")
    username, password = _decode_auth_string(credentials)
    LOGGER.info("Checking for existing account: %s", username)
    account = _get_account_information(username)
    LOGGER.info("Checking if account password matches")
    if _password_correct(password, account):
        claims = {
                'username': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
                'nbf': datetime.datetime.utcnow() + datetime.timedelta(seconds=2)
                }
        LOGGER.info("Generating JST for: %s", username)
        return jwt.encode(claims, os.getenv('APP_AUTH_KEY'), 'HS256')
    raise NotAuthorizedError("Incorrect password")


def _decode_auth_string(auth_string: str) -> (str, str):
    """Decode the provided auth string as a username password pair
    Arguments:
        auth_string: [str] base64 encoded string to decode as a username+password
    Returns:
        [tuple] containing the username and password pair
    Raises:
        NotAuthorizedError -- if the credentials could not be decoded
    """
    try:
        LOGGER.info('Decoding the provided auth string')
        raw_creds = base64.b64decode(auth_string.encode('utf-8')).decode('utf-8').split(':')
        return (raw_creds[0], raw_creds[1])
    except (ValueError, binascii.Error, IndexError) as err:
        LOGGER.error("Could not decode auth string: %s", str(err))
        raise NotAuthorizedError("Invalide credentials") from err


def _password_correct(password: str, account: IdeaBankAccount) -> bool:
    """Check if the provided password is correct
    Arguments:
        password: [str] the password to check
        account: [IdeaBankAccount] the oracle validating password correctness
    Returns:
        [bool] True is correct, otherwise False
    """
    expected = account[IdeaBankAccount.AUTHORIZER_ATTRIBUTE_KEY]
    return secrets.compare_digest(
            hashlib.sha256(f'{password}{expected["Salt"]}'.encode()).hexdigest(),
            expected["Password"]
            )


def _get_account_information(account_name: str) -> IdeaBankAccount:
    """Obtain the account information needed to validate the credentials
    Arguments:
        account_name: [str] username of the account to obtain
    Returns:
        [IdeaBankAccount] of the specified account name
    Raises:
        NotAuthorizedError -- if no account exists
    """
    try:
        LOGGER.info('Getting account information for: %s', account_name)
        return IdeaBankAccountsTable().get_from_table({
            IdeaBankAccount.PARTITION_KEY: account_name
            })
    except DataLinkTableScanFailure as err:
        LOGGER.error("Cannot get account information for nonexistent account")
        raise NotAuthorizedError(f'No account found: {account_name}') from err


def validate_claims(creds: dict) -> bool:
    """Validate the claims presented in the given JWT
    Arguments:
        creds: [dict] containing a JWT and the user it claims to be for
    Returns:
        [bool]: True if claims can be validated, False otherwise
    """
    try:
        token = creds.get('jwt')
        token_for = creds.get('username')
        if not token or not token_for:
            LOGGER.info("No token provided to validate")
            return False
        claims = jwt.decode(
                token,
                os.getenv('APP_AUTH_KEY'),
                'HS256'
                )
        LOGGER.info("Token formatted correctly. Verifying ownership")
        return claims['username'] == token_for
    except (jwt.exceptions.ImmatureSignatureError, jwt.exceptions.ExpiredSignatureError) as err:
        LOGGER.error("Claim immature or expired: %s", str(err))
        return False
    except jwt.exceptions.DecodeError as err:
        LOGGER.error("Provided token could not be decoded: %s", str(err))
        return False


def handler(event, context):  # pylint:disable=unused-argument
    """Handler function for the auth web2 user microservice"""
    try:
        key_type, creds = extract_from_body(event['body'])
        if key_type == AuthKeyType.USERPASSPAIR.value:
            # This is a username:password string. Verify and create claims
            return make_response(
                    status=200,
                    body={'sucess': {'jwt': validate_credentials(creds)}}
                    )
        if key_type == AuthKeyType.WEBTOKEN.value:
            # This is JWT string. Validate claims
            if validate_claims(creds):
                return make_response(
                        status=200,
                        body={'success': {'message': 'Token is valid'}}
                        )
        # We don't know what this is. Forbid it
        raise NotAuthorizedError(f"Unknown key type: {key_type}")
    except NotAuthorizedError as err:
        LOGGER.error(str(err))
        return make_response(
                status=401,
                body={'error': {'message': f'Unauthorized: {str(err)}'}}
                )
    except DataLinkTableInteractionException as err:
        LOGGER.error("Database did not respond")
        return make_response(
                status=503,
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
        'Access-Control-Allow-Methods': 'POST'
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
