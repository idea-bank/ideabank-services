"""
    :module name: exceptions
    :module summary: exception classes for the ideabank webapi package
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""


class BaseIdeaBankAPIException(Exception):
    """Base class for all other package exceptions"""


class IdeaBankDataServiceException(BaseIdeaBankAPIException):
    """Base exception for data service exceptions"""


class NoQueryToRunError(IdeaBankDataServiceException):
    """Exception raised when attempting to execute no query"""


class NoeSessionToQueryOnError(IdeaBankDataServiceException):
    """Exception raised when attempting to run queries without a session"""


class IdeaBankEndpointHandlerException(BaseIdeaBankAPIException):
    """Base exception for endpoint handlers"""


class IdeaBankDataModelingException(BaseIdeaBankAPIException):
    """Base exception for data modeling errors"""
