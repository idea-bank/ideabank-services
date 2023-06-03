"""
    :module name: service
    :module summary: collection of classes that provide access to data services
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

from enum import Enum

from .querydb import QueryService
from .s3crud import S3Crud
from .accounts import AccountsDataService
from .concepts import ConceptsDataService
from .engage import EngagementDataService


class RegisteredService(Enum):
    """Enumeration of registered services"""
    RAW_DB = QueryService
    RAW_S3 = S3Crud
    ACCOUNTS_DS = AccountsDataService
    CONCEPTS_DS = ConceptsDataService
    ENGAGE_DS = EngagementDataService
