"""
    :module name: artifacts
    :module summary: Models for data entities that are accepted and sent
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import re

from pydantic import BaseModel, validator, HttpUrl  # pylint:disable=no-name-in-module

LOGGER = logging.getLogger(__name__)


class IdeaBankArtifact(BaseModel):  # pylint:disable=too-few-public-methods
    """Base class for all data entity representable by this API"""


class CredentialSet(IdeaBankArtifact):  # pylint:disable=too-few-public-methods
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
    def validate_display_name(cls, value):  # pylint:disable=no-self-argument
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
    def validate_password(cls, value):  # pylint:disable=no-self-argument
        """Verifies password is of appropriate length"""
        if re.match(cls.password_format(), value):
            LOGGER.debug("Password length is appropriate")
            return value
        LOGGER.debug("Password length is inappropriate")
        raise TypeError(
                "Password must be at least 8 characters and "
                "consist of letters AND numbers"
                )


class AccountRecord(BaseModel):  # pylint:disable=too-few-public-methods
    """Models a secure version of credentials that can be saved to the db"""
    display_name: str
    password_hash: str
    salt_value: str

    @validator('password_hash')
    def is_valid_hash(cls, value):  # pylint:disable=no-self-argument
        """Verifies hash digest format"""
        if re.match(cls.hex_string(), value):
            LOGGER.debug("Password hash is valid")
            return value
        LOGGER.debug("Password hash is not valid")
        raise TypeError(
                "Hash value is not a hexadecimal of length 64"
                )

    @validator('salt_value')
    def is_valid_hex(cls, value):  # pylint:disable=no-self-argument
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


class AuthorizationToken(IdeaBankArtifact):  # pylint:disable=too-few-public-methods
    """Represent the presentation of a authorization token
    Attributes:
        token: authorization being presented
        presenter: name of entity presenting AND claiming ownershop of token
    """
    token: str
    presenter: str


class ProfileView(IdeaBankArtifact):  # pylint:disable=too-few-public-methods
    """Represent the publicly visible information of an account
    Attributes:
        preferred_name: name of the account user
        biography: textual discription of user introduction
        avatar_url: link to view account avatar
    """
    preferred_name: str
    biography: str
    avatar_url: HttpUrl
