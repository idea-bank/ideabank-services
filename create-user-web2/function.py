"""
    :module_name: function
    :module_summary: Web2 user creation microservice
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

#import uuid
#import json
from dataclasses import dataclass


def handler(event, context):
    """
        A microservice that creates a new idea bank user account using traditional web2 credentials
    """
    print(event)
    print(context)
    return "Hello from lambda!"

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

def parse_event(event: dict) -> UserAccount:
    """
        Parse the data passed to the service as an event object into a more useful state
        :arg event: the event object triggering this service
        :arg type: dict
        :returns: usable data
        :rtype: UserAccount
    """
    print(event)
