"""
    :module_name: function
    :module_summary: Web2 user creation microservice
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import uuid
import json
import base64
import secrets
import hashlib
from dataclasses import dataclass

LOGGER = None
LOG_HANDLER = None
LOG_FORMAT = None


def handler(event, context): #pylint: disable=unused-argument
    """
        A microservice that creates a new idea bank user account using traditional web2 credentials
    """
    set_up_logging()
    return {
            'status': 200,
            'headers': headers(),
            'body': json.dumps(parse_event(event))
            }

class MissingRequireInformationError(Exception):
    """
        Raised when required information to complete an action is missing
    """

class InformationNotInterpretableError(Exception):
    """
        Raised when information cannot be deciphered
    """

@dataclass
class Web2AuthKey:
    """
        class representing a web2 authkey for a user
    """
    email: str
    pass_hash: str
    salt: str

@dataclass
class UserAccount:
    """
        class representing an ideabank user account
    """
    uuid: str
    display_name: str
    auth_keys: dict

def headers() -> dict:
    """
        Generate the headers to be included in the response, including any COR related ones
    """
    return {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST'
            }

def set_up_logging() -> None:
    """
        Set up logging facilities for each run
    """
    global LOGGER, LOG_HANDLER, LOG_FORMAT # pylint: disable=global-statement
    LOGGER = logging.getLogger('create-user-web2-service')
    LOGGER.setLevel(logging.DEBUG)
    LOG_HANDLER = logging.StreamHandler()
    LOG_HANDLER.setLevel(logging.DEBUG)
    LOG_FORMAT = logging.Formatter('[%(asctime)s:%(levelname)s] - %(message)s')
    LOG_HANDLER.setFormatter(LOG_FORMAT)
    LOGGER.addHandler(LOG_HANDLER)

def parse_event(event: dict) -> UserAccount:
    """
        Parse the data passed to the service as an event object into a more useful state
        :arg event: the event object triggering this service
        :arg type: dict
        :returns: usable data
        :rtype: UserAccount
    """
    LOGGER.info("Parsing the event object for information required to create a new user")
    return UserAccount(
            _generate_unique_id(),
            _extract_display_name_from_event(event)
            _extract_authkey_from_event(event)
            )

def _generate_unique_id() -> str:
    """
        Generate a UUID for the new user
        :returns: UUID
        :rtype: str
    """
    LOGGER.info("Generating a random UUID for the new user")
    return str(uuid.uuid())

def _extract_display_name_from_event(event) -> str:
    """
        Extract the display name the event information
        :arg event: the event object triggering this service
        :arg type: dict
        :returns: the new user's display name
        :rtype: str
        :raises: MissingRequiredInformationError if no display name is found
    """
    try:
        LOGGER.info("Extracting display name for new user")
        return event['display_name']
    except KeyError as err:
        LOGGER.error("Could not find the display name for new user")
        raise MissingRequiredInformationError() from err

def _extract_authkey_from_event(event) -> {str: Web2AuthKey}:
    """
        Extract the web2 authkey from the event information
        :arg event: the event object triggering this service
        :arg type: dict
        :returns; the new user's web2 authkey
        :rtype: dict
        :raises: InformationNotInterpretableError if valid authkey cannot be deciphered
        :raises: MissingRequiredInformationError if no credentials are found
    """
    try:
        LOGGER.info("Extracting the auth key for new user")
        username, password = _decode_credentials(event['credentials'])
        salt = _generate_user_salt()
        passkey = _hash_passkey(password, salt)
        return {
                'web2' : Web2AuthKey(username, passkey, salt)
                }
    except KeyError as err:
        LOOGER.error("Could not find the credentials for new user")
        raise MissingRequiredInformationError() from err
    
def _decode_credentials(encoded: str) -> (str, str):
    """
        Decode the base64 encoded string representing credentials asn `email:password`
        :arg encoded: the encoded string
        :arg type: str
        :returns: the credential pair
        :rtype: tuple (str, str)
    """
    LOGGER.info('Decoding the credential string')
    decoded = base64.b64decode(encoded.encode('utf-8')).decode().split(':') 
    if len(decoded) != 2:
        raise InformationNotInterpretableError(
                f"Extraneous parts detected in encoded credentials string: Expected 2, got {len(decoded)}"
                )
    return decoded[0], decoded[1]

def _generate_user_salt() -> str:
    """
        Generate a salt value for the new user
        :returns: a salt value
        :rtype: str
    """
    return secrets.token_hex()

def _hash_passkey(password: str, salt: str) ->:
    """
        Hash the given password and salt
        :arg password: the user provided password
        :arg salt: the randomly generated extensions for additional security
        :arg type: str
        :arg type: str
        :returns: hashed passkey
        :rtype: str
    """
    return hashlib.sha256(f'{password}{salt}'.encode('utf-8')).hexdigest()


