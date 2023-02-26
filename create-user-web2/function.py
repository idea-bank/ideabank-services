"""
    :module_name: function
    :module_summary: #TODO
    :module_author: #TODO
"""

import sys

def handler(event, context):
    """A function that returns a simple greeting response"""
    return {
        "sysinfo": sys.version,
        "event": event,
        "context": str(context)
    }
