"""
    :module_name: function
    :module_summary: main function execution logic
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import os
import json
import base64
import binascii
from dataclasses import dataclass
from uuid import uuid4
from hashlib import sha256
from secrets import token_hex

import boto3
import botocore

LOGGER = logging.getLogger(__name__)
if os.getenv('ENV') == 'prod':
    LOGGER.setLevel(logging.INFO)
else:
    LOGGER.setLevel(logging.DEBUG)

LOG_HANDLER = logging.StreamHandler()
if os.getenv('ENV') == 'prod':
    LOG_HANDLER.setLevel(logging.INFO)
else:
    LOG_HANDLER.setLevel(logging.DEBUG)

LOG_FORMAT = logging.Formatter('[%(asctime)s|%(name)s|%(levelname)s] - %(message)s')
LOG_HANDLER.setFormatter(LOG_FORMAT)
LOGGER.addHandler(LOG_HANDLER)

class MissingInformationException(Exception):
    """
        Exception raised when required information is missing from service event payload
    """

class MalformedDataException(Exception):
    """
        Excpetion raised when information format is incorrect or data cannot be understood
    """

class UserCreationException(Exception):
    """
        Exception raised when user creation fails
    """

@dataclass
class NewUser:
    """
        Dataclass representing a new user account to create
    """
    uuid: str
    display_name: str
    authkeys: dict

    def __init__(self, name, **keys):
        self.uuid = uuid4()
        self.display_name = name
        self.authkeys = keys
        LOGGER.info('Created a new user with given information and a unique identifier')
        LOGGER.debug('\tUnique identifier: %s\n\tDisplay name: %s', str(self.uuid), name)

@dataclass
class Web2Key:
    """
        Dataclass representing the credentials of a new web2 user
    """
    email: str
    pass_hash: str
    salt: str

    def __init__(self, raw_user, raw_pass):
        LOGGER.info('Generating a new web authorization key for the new user')
        self.email = raw_user
        self.pass_hash, self.salt = self.__mix_it_up(raw_pass)

    def __mix_it_up(self, thing_to_mix: str) -> (str, str):
        """
            Helper method to ensure password is not stored as plain text
            :arg thing_to_mix: the password to scramble
            :arg type: str
            :returns: hash and salt used
            :rtype: (str, str)
        """
        user_salt = token_hex()
        user_hash = sha256(f'{thing_to_mix}{user_salt}'.encode('utf-8')).hexdigest()
        return user_hash, user_salt

class InputDecoder:
    """
        A class that helps decode event data
    """
    def __init__(self, event_data: dict):
        LOGGER.info('Received input payload, ready to extract and decode')
        self._input = event_data
        self._display_name = None
        self._credential_string = None

    def extract(self):
        """
            Extract the required data from the event
            :returns: updated input decoder object
            :rtype: self
            :raises: MissingInformationException if expected information is missing
        """
        try:
            self._display_name = self._input['displayName']
            self._credential_string = self._input['credentials']
            LOGGER.info('Extracting required information from input')
            LOGGER.debug('\tDisplay name: %s\n\tEncoded credentials: %s',
                         self._display_name,
                         self._credential_string
                         )
            return self
        except KeyError as err:
            LOGGER.error('Input did not contain the required key: %s', str(err))
            raise MissingInformationException(f"Missing required information: `{err}`") from err

    def decode(self):
        """
            Decode the given credential string as a user/pass combination
            :arg credential_string: base64 encoded string with format `user:pass`
            :returns: mapping of decoded user / pass combinatino
            :rtype: dict
            :raises: MalformedDataException if decode fails or credential string is undecipherable
        """
        if not self._display_name or not self._credential_string:
            LOGGER.error('Nothing to decode. Stop.')
            raise MissingInformationException(
                    "Cannot decode unknown credentials. Perhaps you forgot to call extract()?"
                )
        try:
            LOGGER.info('Decoding the provided new user credentials')
            decoded = base64.b64decode(self._credential_string.encode('utf-8')).decode('utf-8')
            user_email, pass_phrase = decoded.split(':', 1)
            return {
                    'display_name': self._display_name,
                    'user_email': user_email,
                    'user_pass': pass_phrase
                    }
        except (ValueError, binascii.Error) as err:
            LOGGER.error('Failed to decode the provided credentials')
            raise MalformedDataException("Could not decipher credential string") from err

class IdeaBankUser:
    """
        Class that interfaces with DynamDB IdeaBankUsers Table
    """
    TABLE_NAME="IdeaBankUsers"

    def __init__(self):
        if os.getenv('ENV') == 'prod':
            LOGGER.warning('Using production settings')
            self._resource = boto3.client('dynamodb')
        else:
            LOGGER.warning('Using local setings')
            self._resource = boto3.client('dynamodb', endpoint_url='http://localhost:8000')

    @property
    def table(self):
        """
            getter for the DynamoDB table name to be user
            :returns: DynamoDb tablename
            :rtype: str
        """
        return self.TABLE_NAME

    def create_user(self, new_user: NewUser) -> None:
        """
            Create the user user in the IdeaBankUser table
            :arg new_user: the user to create
            :arg type: NewUser
            :returns: nothing
            :rtype: None
            :raises: ClientError if the db interaction fails for any reason
        """
        try:
            LOGGER.info('Attempting to create a record for the new user...')
            self._resource.put_item(
                TableName=self.table,
                Item={
                    'UserID': {
                        'S': str(new_user.uuid)
                    },
                    'DisplayName': {
                        'S': new_user.display_name
                    },
                    'Authkeys': { 
                        'M': {
                            'Web2': {
                                'M': {
                                    'Email': {
                                        'S': new_user.authkeys['web2'].email
                                    },
                                    'PasswordHash': {
                                        'S': new_user.authkeys['web2'].pass_hash
                                    },
                                    'Salt': {
                                        'S': new_user.authkeys['web2'].salt
                                    }
                                }
                            }
                        }
                    }
                }
            )
            LOGGER.info('New user record was successfully created')
        except botocore.exceptions.ClientError as err:
            LOGGER.error(
                "Couldn't add new user %s to table %s. Here's why: %s: %s",
                new_user.display_name, self.table,
                err.response['Error']['Code'], err.response['Error']['Message']
                    )
            raise UserCreationException from err

def handler(event, context): #pylint:disable=unused-argument
    """
        Handler function for the create web2 user microservice
    """
    try:
        LOGGER.info('Start service: create-user-web2')
        LOGGER.debug('Event info: %s', json.dumps(event, indent=4))
        new_user_data = InputDecoder(event).extract().decode()
        key = Web2Key(new_user_data['user_email'], new_user_data['user_pass'])
        user = NewUser(new_user_data['display_name'], **{'web2': key})
        IdeaBankUser().create_user(user)
        return user_creation_confirmation()
    except (MissingInformationException, MalformedDataException) as err:
        return bad_request_response(err)
    except UserCreationException as err:
        return bad_gateway_response(err)


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

def bad_request_response(error: Exception):
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
                    'message': str(error)
                    }
                })
            }

def bad_gateway_response(error: Exception):
    """
        Timeout response
    """
    LOGGER.error('Service could not interact with DynamoDB')
    return {
            'isBase64Encoded': False,
            'statusCode': 502,
            'headers': headers(),
            'body': json.dumps({
                'error': {
                    'message': str(error)
                    }
                })
            }
