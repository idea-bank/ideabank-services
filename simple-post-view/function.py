"""
    :module_name: function
    :module_summary: service to deliver high-level post information view
    :module_author: Utsav Sampat
"""

import json
import boto3
from ideadb_handler import *

def handler(event, context):
    """
        Service to query high-level post details from the database
    """
    _input = event['body']
    if not 'IdeaPostID' in _input: raise NotValidParameters('IdeaPostID')
    if not 'IdeaAuthorID' in _input: raise NotValidParameters('IdeaAuthorID')

    try:
        posts = IdeaPostTable()
        posts.load()

        post = posts.get_post(_input['IdeaPostID'], _input['IdeaAuthorID'])
        return {
            'status': 200,
            'body': json.dumps(post)
        }
    except NotValidParameters as error:
        return {
            'status': 400,
            'body': str(error)
        }
    except DatabaseException as error:
        return {
            'status': 500,
            'body': str(error)
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