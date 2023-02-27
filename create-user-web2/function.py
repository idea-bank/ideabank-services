"""
    :module_name: function
    :module_summary: Web2 user creation microservice
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
#import uuid
#import json
#import base64
from dataclasses import dataclass

LOGGER = None
LOG_HANDLER = None
LOG_FORMAT = None


def handler(event, context): #pylint: disable=unused-argument
    """
        A microservice that creates a new idea bank user account using traditional web2 credentials
    """
    set_up_logging()
    LOGGER.info('Test log')
    return 'Hello from lambda!'


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
    print(event)
