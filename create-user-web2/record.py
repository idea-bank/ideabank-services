"""
    :module_name: record
    :module_summary: class for interfacing with DynamoDB and creating a user
    :module_author: Nathan Mendoz (nathancm@uci.edu)
"""

import os
import boto3

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

    def list_tables(self):
        print(self._resource.list_tables())
