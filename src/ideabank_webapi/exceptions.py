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


class DuplicateRecordException(IdeaBankDataServiceException):
    """Raised when attempted to insert a duplicate data record"""


class InvalidReferenceException(IdeaBankDataServiceException):
    """Raised when attempting to write a record that violates referential integrity"""


class IdeaBankEndpointHandlerException(BaseIdeaBankAPIException):
    """Base exception for endpoint handlers"""


class NoSuchHandlerException(IdeaBankEndpointHandlerException):
    """Exception raised when requesting construction of a nonexistant handler"""


class HandlerNotIdleException(IdeaBankEndpointHandlerException):
    """Exception raised when handler attempts to receive a request when not idle"""


class PrematureResultRetrievalException(IdeaBankEndpointHandlerException):
    """Exception raised when handler results are read before they are ready"""


class NoRegisteredProviderError(IdeaBankEndpointHandlerException):
    """Exception raised when a service provider is requested, but not registered"""


class NotAuthorizedError(IdeaBankEndpointHandlerException):
    """Exception raised when an authorization check fails"""


class RequestedDataNotFound(IdeaBankEndpointHandlerException):
    """Exception raised when request query returns non results"""


class InvalidCredentialsException(IdeaBankEndpointHandlerException):
    """Exception raised when credentials verifications fails"""


class IdeaBankDataModelingException(BaseIdeaBankAPIException):
    """Base exception for data modeling errors"""
