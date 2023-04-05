import json
import logging
import time
import boto3
from boto3.dynamodb.conditions import Key
from contextlib import closing

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

LOG_HANDLER = logging.StreamHandler()
LOG_HANDLER.setLevel(logging.DEBUG)

LOG_FORMAT = logging.Formatter('[%(asctime)s|%(name)s|%(levelname)s] - %(message)s')
LOG_HANDLER.setFormatter(LOG_FORMAT)
LOGGER.addHandler(LOG_HANDLER)

# This should be an environment variable
ENDPOINT_URL = 'http://localhost:8000'

class IdeaPostTable:
    """
        Encapsulates an Amazon DynamoDB table of post data.
    """
    TABLE_NAME = "IdeaPost"

    def get_post(self, IdeaPostID, IdeaAuthorID, fields):
        try:
            LOGGER.debug("Attempting to get post with IdeaPostID: %s and IdeaAuthorID: %s", IdeaPostID, IdeaAuthorID)
            with closing(boto3.client('dynamodb', endpoint_url=ENDPOINT_URL)) as client:
                response = client.get_item(
                    TableName=self.TABLE_NAME, 
                    Key={
                        'IdeaPostID': {'S': IdeaPostID}, 
                        'IdeaAuthorID': {'S': IdeaAuthorID}
                    },
                    ProjectionExpression=','.join(fields)
                )
        
        except Exception as err: 
            LOGGER.error("Failed to get post with IdeaPostID: %s and IdeaAuthorID: %s with error: %s", IdeaPostID, IdeaAuthorID, str(err))
            raise DatabaseException(err)
        
        else:
            if not 'Item' in response: 
                LOGGER.debug("Item with IdeaPostID: %s and IdeaAuthorID: %s was NOT FOUND!", IdeaPostID, IdeaAuthorID)
                return {}
            LOGGER.debug("Item found: %s", json.dumps(response['Item'], indent=4))
            return response['Item']

    def add_post(self, data):
        try:
            LOGGER.debug("Adding post with data: %s", json.dumps(data, indent=4))
            data['created_at'] = {'N': str(int(time.time()*1000))}

            with closing(boto3.client('dynamodb', endpoint_url=ENDPOINT_URL)) as client:
                response = client.put_item(TableName=self.TABLE_NAME, Item=data)
        except Exception as err: 
            LOGGER.error("Failed to get post with IdeaPostID: %s and IdeaAuthorID: %s with error: %s", IdeaPostID, IdeaAuthorID, str(err))
            raise DatabaseException(err)
        else: return response
    
##################### EXCEPTION #####################
class DatabaseException(Exception):
    """
        Raised when there is database error
    """
#####################################################