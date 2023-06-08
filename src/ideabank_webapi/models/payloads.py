"""
    :module name: payloads
    :module summary: classes the model the payloads accepted by endpoint handlers
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
from typing import Union, List, Dict, Optional

from pydantic import BaseModel, Extra, UUID4, constr  # pylint:disable=no-name-in-module

from .artifacts import (
        AuthorizationToken,
        ConceptLinkRecord,
        AccountFollowingRecord,
        ConceptLikingRecord,
        ConceptComment
        )

# pylint:disable=too-few-public-methods
# pylint:disable=no-self-argument

LOGGER = logging.getLogger(__name__)


class EndpointPayload(BaseModel):
    """Base payload model for data passed to endpoint handlers"""
    class Config:
        """Some global configuration options for models"""
        extra: Extra = Extra.forbid
        allow_mutation: bool = False
        anystr_strip_whitespace: bool = True


class ConceptDataPayload(EndpointPayload):
    """Models a payload that allows creation of of new concept"""
    author: constr(min_length=3, max_length=64, regex=r"^[\w]{3,64}$")
    title: constr(min_length=1, max_length=128, regex=r"^[\w\-]{1,128}$")
    description: constr(min_length=1)
    diagram: Dict[str, List[Dict[str, Union[int, str]]]]


class AuthorizedPayload(EndpointPayload):
    """Models a payload that includes an authorization token"""
    auth_token: AuthorizationToken


class CreateConcept(AuthorizedPayload, ConceptDataPayload):
    """Models a concept payload with required authorization information"""


class EstablishLink(AuthorizedPayload, ConceptLinkRecord):
    """Models a concept linking payload with require authorization info"""


class ConceptRequest(EndpointPayload):
    """Models a requests to find a particular concept and control its return form"""
    author: constr(min_length=3, max_length=64, regex=r"^[\w]{3,64}$")
    title: constr(min_length=1, max_length=128, regex=r"^[\w\-]{1,128}$")
    simple: bool


class FollowRequest(AuthorizedPayload, AccountFollowingRecord):
    """Models a request for one user to start following another"""


class UnfollowRequest(AuthorizedPayload, AccountFollowingRecord):
    """Models a request for one user to stop following another"""


class LikeRequest(AuthorizedPayload, ConceptLikingRecord):
    """Models a request for a user to start liking a concept"""


class UnlikeRequest(AuthorizedPayload, ConceptLikingRecord):
    """Models a request for a user to stop liking a concept"""


class CreateComment(AuthorizedPayload, ConceptComment):
    """Models a request for a user to leave a comment on a concept"""
    concept_id: constr(regex=r"^[\w]{3,64}/[\w\-]{1,128}$")
    response_to: Optional[UUID4]
