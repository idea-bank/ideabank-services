"""
    :module name: artifacts
    :module summary: Models for data entities that are accepted and sent
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import re
import datetime
from typing import Sequence, Union, Dict, List
from enum import Enum

from pydantic import BaseModel, validator, HttpUrl, Field  # pylint:disable=no-name-in-module

LOGGER = logging.getLogger(__name__)

# pylint:disable=too-few-public-methods
# pylint:disable=no-self-argument


def unix_epoch() -> datetime.datetime:
    """Utility function for returning a datetime representing the unix epoch
    Returns:
        [datetime] 1970, 1, 1
    """
    return datetime.datetime.fromtimestamp(0, datetime.timezone.utc)


def utc_now() -> datetime.datetime:
    """Utility function for returning a datetime representing current utc timezone
    Returns:
        [datetime] utcnow
    """
    return datetime.datetime.now(tz=datetime.timezone.utc)


class IdeaBankArtifact(BaseModel):
    """Base class for all data entity representable by this API"""


class EndpointResponse(BaseModel):
    """Base class for all response model produced by this API"""
    code: int
    body: Union[Sequence[IdeaBankArtifact], IdeaBankArtifact]


class EndpointErrorMessage(IdeaBankArtifact):
    """Wrapper around a error message generated by endpoint handlers"""
    err_msg: str


class EndpointInformationalMessage(IdeaBankArtifact):
    """Wrapper around an informational message generated by endpoint handlers"""
    msg: str


class CredentialSet(IdeaBankArtifact):
    """Represents a set of credentials used for account creation/authentication
    Attributes:
        display_name: display name of the user
        password: password of the user
    """
    display_name: str
    password: str

    @staticmethod
    def display_name_format():
        """A regular expression for validating display name formats"""
        return re.compile(r"^[\w]{3,64}$")

    @staticmethod
    def password_format():
        """A regular expression for validating password formats"""
        return re.compile(r"^[\w]{8,32}$")

    @validator('display_name')
    def validate_display_name(cls, value):
        """Verifies dissplay name meets format"""
        if re.match(cls.display_name_format(), value):
            LOGGER.debug("Display name format is valid")
            return value
        LOGGER.debug("Display name format is invalid")
        raise TypeError(
                "Display name must be between 3 and 64 character "
                "and consists of letters, numbers and underscores"
                )

    @validator('password')
    def validate_password(cls, value):
        """Verifies password is of appropriate length"""
        if re.match(cls.password_format(), value):
            LOGGER.debug("Password length is appropriate")
            return value
        LOGGER.debug("Password length is inappropriate")
        raise TypeError(
                "Password must be at least 8 characters and "
                "consist of letters AND numbers"
                )


class AccountRecord(BaseModel):
    """Models a secure version of credentials that can be saved to the db"""
    display_name: str
    password_hash: str
    salt_value: str

    @validator('password_hash')
    def is_valid_hash(cls, value):
        """Verifies hash digest format"""
        if re.match(cls.hex_string(), value):
            LOGGER.debug("Password hash is valid")
            return value
        LOGGER.debug("Password hash is not valid")
        raise TypeError(
                "Hash value is not a hexadecimal of length 64"
                )

    @validator('salt_value')
    def is_valid_hex(cls, value):
        """Verifies salte value formath"""
        if re.match(cls.hex_string(), value):
            LOGGER.debug("Salt value is valid.")
            return value
        LOGGER.debug("Salt value is invalid.")
        raise TypeError(
                "Hash value is not a hexadecimal of length 64"
                )

    @staticmethod
    def hex_string() -> re.Pattern:
        """A regular expression matching against a valid hex string of lenth 64"""
        return re.compile(r'^[0-9A-Fa-f]{64}$')


class AuthorizationToken(IdeaBankArtifact):
    """Represent the presentation of a authorization token
    Attributes:
        token: authorization being presented
        presenter: name of entity presenting AND claiming ownershop of token
    """
    token: str
    presenter: str


class ProfileView(IdeaBankArtifact):
    """Represent the publicly visible information of an account
    Attributes:
        preferred_name: name of the account user
        biography: textual discription of user introduction
        avatar_url: link to view account avatar
    """
    preferred_name: str
    biography: str
    avatar_url: HttpUrl


class ConceptSimpleView(IdeaBankArtifact):
    """Represents a simple view of an idea bank concept
    Attributes:
        identifier: the {author}/{title} formatted string identifying a concept
        thumbnail_url: link to view the concept thumbnail
    """
    identifier: str
    thumbnail_url: HttpUrl


class ConceptFullView(IdeaBankArtifact):
    """Represents the full view of an idea bank concept
    Attributes:
        author: display name of the user who created the idea
        title: name of the idea given by the creating user
        description: textual description of idea
        diagram: JSON representation of idea's component graph
        thumbnail_url: link to view thumbnail of idea
    """
    author: str
    title: str
    description: str
    diagram: Dict[str, List[Dict[str, Union[int, str]]]]
    thumbnail_url: HttpUrl


class ConceptLinkRecord(IdeaBankArtifact):
    """Represents a link between two idea bank with a parent-child relation
    Attributes:
        ancestor: the {author}/{title} formatted string identifying the parent
        descendant: the {author}/{title} formatted string identifying the child
    """
    ancestor: str
    descendant: str


class FuzzyOption(str, Enum):
    """Enumeration of options for fuzzy searching of concepts"""
    NONE = 'none'
    TITLE = 'title-only'
    AUTHOR = 'author-only'
    ALL = 'all'


class ConceptSearchQuery(IdeaBankArtifact):
    """Represents a collection of parameters for searching idea bank concepts
    Attributes:
        author: [str] the author of the search query to find
        title:  [str] the title of the search query to find
        not_before: [datetime] the timestamp marking the start of the range to search in
        not_after: [datetime] the timestamp marking the end of the range to search in
        fuzzy: [FuzzyOption] level of fuzziness to use during search
    """
    author: str
    title: str
    not_before: datetime.datetime = Field(default_factory=unix_epoch)
    not_after: datetime.datetime = Field(default_factory=utc_now)
    fuzzy: FuzzyOption = FuzzyOption.NONE
