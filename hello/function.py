"""
    :module_name: function
    :module_summary: a simple aws lambda function
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

import sys
import json
import os

def handler(event, context): #pylint:disable=unused-argument
    """A simple function that returns system/event/context info with CORS headers"""
    return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps({
                'sysinfo': sys.version,
                'context': os.getenv('ENV')
            })
        }
