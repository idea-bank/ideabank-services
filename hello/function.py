"""
    :module_name: function
    :module_summary: a simple aws lambda function
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

import sys

def handler(event, context):
    """A function that returns a simple greeting response"""
    return f'Hello from AWS lambda using Python {sys.version}!'
