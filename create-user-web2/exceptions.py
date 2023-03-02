"""
    :module_name: exceptions
    :module_summary: exception classes for create web2 user service
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

class MissingInformationException(Exception):
    """
        Exception raised when required information is missing from service event payload
    """

class MalformedDataException(Exception):
    """
        Excpetion raised when information format is incorrect or data cannot be understood
    """
