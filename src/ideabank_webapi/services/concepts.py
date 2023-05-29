"""
    :module name: concepts
    :module summary: Unified service provider for concepts information
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
from typing import Union, Dict, List

from sqlalchemy import select, insert
from sqlalchemy.sql.expression import Select, Insert

from .querydb import QueryService
from .s3crud import S3Crud
from ..models.schema import Concept, ConceptLink

LOGGER = logging.getLogger(__name__)


class ConceptsDataService(QueryService, S3Crud):
    """Provider for account information."""

    def __init__(self):
        QueryService.__init__(self)
        S3Crud.__init__(self)

    @staticmethod
    def create_concept(
            title: str,
            author: str,
            description: str,
            diagram: Dict[str, List[Dict[str, Union[int, str]]]]
            ) -> Insert:
        """Builds an insertion statement to create a new concept
        Arguments:
            title: [str] title of the new concept
            author: [str] author of the new concept
            description: [str] textual description of the new concept
            diagram: JSON representation of the concept's component graph
        Returns:
            [Insert] the SQLAlchemy insertion statement
            """
        LOGGER.info("Built query to create a concept record")
        return insert(Concept) \
            .values(
                    title=title,
                    author=author,
                    description=description,
                    diagram=diagram
                    ) \
            .returning(
                    Concept.identifier
                    )

    @staticmethod
    def find_exact_concept(title: str, author: str) -> Select:
        """Builds a selection statement to query for a specific concept
        Arguments:
            title: [str] title of the concept to look for
            author: [str] author of the concept to look for
        Returns:
            [Select] the SQLAlchemy selection statement
        """
        LOGGER.info("Built query to select a specific concept")
        return select(Concept) \
            .where(Concept.title == title, Concept.author == author)

    @staticmethod
    def link_existing_concept(parent_identifier: str, child_identifier: str) -> Insert:
        """Builds an insertion statement to create a new link record
        Arguments:
            parent_identifier: [str] id of the parent concept
            child_identifier: [str] id of the child concept
        Returns:
            [Insert] the SQLAlchemy insertion statement
        """
        LOGGER.info("Built query to create a link between concepts")
        return insert(ConceptLink) \
            .values(
                    ancestor=parent_identifier,
                    descendant=child_identifier
                    ) \
            .returning(
                    ConceptLink.ancestor,
                    ConceptLink.descendant
                    )
