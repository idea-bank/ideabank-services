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
        Class that interfaces with DynamDB IdeaBankUsers Table
    """
    TABLE_NAME="IdeaBankUsers"

    def __init__(self):
        if os.getenv('ENVIRONMENT') == 'prod':
            self._resource = boto3.resource('dynamodb')
        else:
            self._resource = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')

    def create_user(self, new_user: NewUser) -> None:
        """
            Create the user user in the IdeaBankUser table
            :arg new_user: the user to create
            :arg type: NewUser
            :returns: nothing
            :rtype: None
            :raises: ClientError if the db interaction fails for any reason
        """
        table = self._resource.Table(self.TABLE_NAME)
        table.put_item(
                Item={
                    'UserID': str(new_user.uuid),
                    'DisplayName': new_user.display_name,
                    'Profile': asdict(new_user.profile),
                    'Authkeys': {
                        'Web2': asdict(new_user.authkeys['web2'])
                        }
                    }
                )
