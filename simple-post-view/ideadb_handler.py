import boto3
from boto3.dynamodb.conditions import Key

# This should be an environment variable
ENDPOINT_URL = 'http://localhost:8000'

class IdeaPostTable:
    """
        Encapsulates an Amazon DynamoDB table of post data.
    """
    def __init__(self):
        try:
            self.dyn_resource = boto3.resource('dynamodb', endpoint_url=ENDPOINT_URL)
            self.table = None
        except Exception as err: raise DatabaseException(err)

    def load(self):
        try:
            self.table = self.dyn_resource.Table('IdeaPost')
            self.table.load()
        except Exception as err: raise DatabaseException(err)
    
    def get_post(self, IdeaPostID, IdeaAuthorID):
        try:
            response = self.table.get_item(Key={'IdeaPostID': IdeaPostID, 'IdeaAuthorID': IdeaAuthorID})
        except Exception as err: raise DatabaseException(err)
        else:
            if not 'Item' in response: return {}
            return response['Item']

    def add_post(self, data):
        try:
            response = self.table.put_item(Item=data)
        except Exception as err: raise DatabaseException(err)
        else: return response
    
##################### EXCEPTION #####################
class DatabaseException(Exception):
    """
        Raised when there is database error
    """
#####################################################