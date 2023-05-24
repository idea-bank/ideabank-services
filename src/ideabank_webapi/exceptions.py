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


class NoSessionToQueryOnError(IdeaBankDataServiceException):
    """Exception raised when attempting to run queries without a session"""


class IdeaBankEndpointHandlerException(BaseIdeaBankAPIException):
    """Base exception for endpoint handlers"""


class HandlerNotIdleException(IdeaBankEndpointHandlerException):
    """Exception raised when handler attempts to receive a request when not idle"""


class NoRegisteredProviderError(IdeaBankEndpointHandlerException):
    """Exception raised when a service provider is requested, but not registered"""


class ProviderMisconfiguredError(IdeaBankEndpointHandlerException):
    """Exception raised when a service provider is not the expected type"""

class IdeaBankDataModelingException(BaseIdeaBankAPIException):
    """Base exception for data modeling errors"""