"""
    :module_name: record
    :module_summary: class for interfacing with DynamoDB and creating a user
    :module_author: Nathan Mendoz (nathancm@uci.edu)
"""

import os
from dataclasses import asdict

import boto3

from utils import NewUser

class IdeaBankUser:
    """
        Class that interfaces with DynamDB IdeaBankUser Table
    """
    TABLE_NAME="IdeaBankUser"

    def __init__(self):
        if os.getenv('ENVIRONMENT') == 'prod':
            self._resource = boto3.client('dynamodb')
        else:
            self._resource = boto3.client('dynamodb', endpoint_url='http://localhost:8000')

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
            self._resource.put_item(
                    TableName=self.TABLE_NAME,
                    Item=asdict(new_user)
                    )
        except boto3.ClientError as err:
            print(err)
            raise
