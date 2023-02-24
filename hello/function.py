"""
    :module_name: function
    :module_summary: a simple aws lambda function
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

import sys
import json

def handler(event, context):
    """A function that returns a simple greeting response"""
    return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps({
                'sysinfo': sys.version,
                'event': event,
                'context': str(context)
            })
        }
