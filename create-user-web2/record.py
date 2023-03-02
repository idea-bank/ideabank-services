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
        self._resource.put_item(
                TableName=self.TABLE_NAME,
                Item={
                    'UserID': {
                        'S': str(new_user.uuid)
                    },
                    'DisplayName': {
                        'S': new_user.display_name
                    },
                    'Authkeys': { 
                        'M': {
                            'Web2': {
                                'M': {
                                    'Email': {
                                        'S': new_user.authkeys['web2'].email
                                    },
                                    'PasswordHash': {
                                        'S': new_user.authkeys['web2'].pass_hash
                                    },
                                    'Salt': {
                                        'S': new_user.authkeys['web2'].salt
                                    }
                                }
                            }
                        }
                    }
                }
            )
