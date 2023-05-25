"""
    :module name: artifacts
    :module summary: Models for data entities that are accepted and sent
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import re
import base64
import binascii

from pydantic import BaseModel, validator, HttpUrl  # pylint:disable=no-name-in-module


class CredentialSet(BaseModel):  # pylint:disable=too-few-public-methods
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
            return value
        raise TypeError(
                "Display name must be between 3 and 64 character "
                "and consists of letters, numbers and underscores"
                )

    @validator('password')
    def validate_password(cls, value):  # pylint:disable=no-self-argument
        """Verifies password is of appropriate length"""
        if re.match(cls.password_format(), value):
            return value
        raise TypeError(
                "Password must be at least 8 characters and "
                "consist of letters AND numbers"
                )


class AuthorizationToken(BaseModel):  # pylint:disable=too-few-public-methods
    """Represent the presentation of a authorization token
    Attributes:
        token: authorization being presented
        presenter: name of entity presenting AND claiming ownershop of token
    """
    token: str
    presenter: str


class ProfileView(BaseModel):  # pylint:disable=too-few-public-methods
    """Represent the publicly visible information of an account
    Attributes:
        preferred_name: name of the account user
        biography: textual discription of user introduction
        avatar_url: link to view account avatar
    """
    preferred_name: str
    biography: str
    avatar_url: HttpUrl
