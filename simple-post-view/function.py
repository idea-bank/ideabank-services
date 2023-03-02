"""
    :module_name: function
    :module_summary: service to deliver high-level post information view
    :module_author: Utsav Sampat
"""

import json
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

def handler(event, context):
    """
        Service to query high-level post details from the database
    """
    if not 'IdeaPostID' in event: raise NotValidParameters('IdeaPostID')
    if not 'IdeaAuthorID' in event: raise NotValidParameters('IdeaAuthorID')
    
    try:
        posts = IdeaPost(boto3.resource('dynamodb', endpoint_url='http://localhost:8000'))
        posts.load()

        post = posts.get_post(event['IdeaPostID'], event['IdeaAuthorID'])
        return {
            'status': 200,
            'headers': headers(),
            'body': json.dumps(post)
        }
    except: raise

###################### EXCEPTIONS ######################
class NotValidParameters(Exception):
    """
        Raised when required parameters are not valid
    """
    def __init__(self, param_name, message=""):
        self.salary = salary
        self.message = f'Parameter "{param_name}" not found'
        super().__init__(self.message)

class PostNotFound(Exception):
    """
        Raised when the post details queried does not exist
    """

class UnknownException(Exception):
    """
        Rased when unknown exception occurs
    """
#########################################################

class IdeaPost:
    """
        Encapsulates an Amazon DynamoDB table of post data.
    """
    def __init__(self, dyn_resource):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.dyn_resource = dyn_resource
        self.table = None

    def load(self):
        try:
            self.table = self.dyn_resource.Table('IdeaPost')
            self.table.load()
        except Exception as err:
            raise UnknownException(err)
    
    def get_post(self, IdeaPostID, IdeaAuthorID):
        try:
            response = self.table.get_item(Key={'IdeaPostID': IdeaPostID, 'IdeaAuthorID': IdeaAuthorID})
        except ClientError as err:
            raise PostNotFound
        else:
            if not 'Item' in response:
                raise PostNotFound
            
            return response['Item']

    def add_post(self, data):
        try:
            response = self.table.put_item(Item=data)
        except Exception as err:
            raise UnknownException(err)
        else:
            return response

def headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST'
    }