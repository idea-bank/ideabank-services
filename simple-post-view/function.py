"""
    :module_name: function
    :module_summary: service to deliver high-level post information view
    :module_author: Utsav Sampat
"""

import logging
import json
import boto3
from ideadb_handler import *

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

LOG_HANDLER = logging.StreamHandler()
LOG_HANDLER.setLevel(logging.DEBUG)

LOG_FORMAT = logging.Formatter('[%(asctime)s|%(name)s|%(levelname)s] - %(message)s')
LOG_HANDLER.setFormatter(LOG_FORMAT)
LOGGER.addHandler(LOG_HANDLER)

SIMPLE_VIEW_FIELDS = [
    'title',
    'created_at',
    'media_links'
]

def handler(event, context):
    """
        Service to query high-level post details from the database
    """
    LOGGER.info("Start service: simple-post-view")
    LOGGER.debug("Event info: %s", json.dumps(event, indent=4))

    try:
        _input = event['body']

        if not 'IdeaPostID' in _input: raise NotValidParameters('IdeaPostID')
        if not 'IdeaAuthorID' in _input: raise NotValidParameters('IdeaAuthorID')

        posts = IdeaPostTable()
        
        LOGGER.info("Attempting to get post by IdeaPostID and IdeaAuthorID...")
        post = posts.get_post(_input['IdeaPostID'], _input['IdeaAuthorID'], fields=SIMPLE_VIEW_FIELDS)
        
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            "body": json.dumps(post)
        }
    
    except NotValidParameters as error:
        LOGGER.error("Request did not have valid parameters: %s", str(error))
        return {
            "isBase64Encoded": False,
            "statusCode": 400,
            "headers": {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            "body": str(error)
        }
    except DatabaseException as error:
        LOGGER.error("There was database error: %s", str(error))
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            "body": str(error)
        }

###################### EXCEPTIONS ######################
class NotValidParameters(Exception):
    """
        Raised when required parameters are not valid
    """
    
    def __init__(self, param_name, message=""):
        self.message = f'Parameter "{param_name}" not found'
        super().__init__(self.message)
#########################################################