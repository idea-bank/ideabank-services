"""
    :module name: payloads
    :module summary: classes the model the payloads accepted by endpoint handlers
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import re
from typing import Union, List, Dict

from pydantic import BaseModel, validator  # pylint:disable=no-name-in-module

from .artifacts import AuthorizationToken, ConceptLinkRecord

# pylint:disable=too-few-public-methods
# pylint:disable=no-self-argument

LOGGER = logging.getLogger(__name__)


class EndpointPayload(BaseModel):
    """Base payload model for data passed to endpoint handlers"""


class ConceptDataPayload(EndpointPayload):
    """Models a payload that allows creation of of new concept"""
    author: str
    title: str
    description: str
    diagram: Dict[str, List[Dict[str, Union[int, str]]]]

    @validator('title')
    def validate_concept_title(cls, value):
        """Ensures submitted titles conform to format"""
        if re.match(cls.title_format(), value):
            LOGGER.info('Title format is valid')
            return value
        LOGGER.error('Title format is invalid')
        raise ValueError(
                'Title must consist of letters, numbers, underscores, and hyphens. '
                'It must also be between 3 and 128 characters'
                )

    @staticmethod
    def title_format() -> re.Pattern:
        """Returns a regular expresion to validate titles for concepts"""
        return re.compile(r'^[\w\-]{3,128}$')


class AuthorizedPayload(EndpointPayload):
    """Models a payload that includes an authorization token"""
    auth_token: AuthorizationToken


class CreateConcept(AuthorizedPayload, ConceptDataPayload):
    """Models a concept payload with required authorization information"""


class EstablishLink(AuthorizedPayload, ConceptLinkRecord):
    """Models a concept linking payload with require authorization info"""
