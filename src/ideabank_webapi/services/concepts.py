"""
    :module name: concepts
    :module summary: Unified service provider for concepts information
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import datetime
from typing import Union, Dict, List

from sqlalchemy import select, insert, literal
from sqlalchemy.sql.expression import Select, Insert

from .querydb import QueryService
from .s3crud import S3Crud
from ..models.schema import Concept, ConceptLink
from ..models.artifacts import FuzzyOption

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
        return select(
                Concept.author,
                Concept.title,
                Concept.description,
                Concept.diagram
                ) \
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

    @staticmethod
    def query_concepts(
            author: str,
            title: str,
            not_before: datetime.datetime,
            not_after: datetime.datetime,
            fuzzy: FuzzyOption
            ) -> Select:
        """Builds a selection statement to query the concept records
        Arguments:
            author: [str] the author the query on
            title: [str] the title to query on
            not_before: [datetime] the start of the time range to query on
            not_after: [datetime] the end of the time range to query on
            fuzzy: [FuzzyOption] controls fuzzy searches on author and title
        Returns:
            [Select] the SQLAlchemy selection statement
        """
        LOGGER.info("Built query to search concept records")
        stmt = select(
                    Concept.identifier
                )
        if fuzzy == FuzzyOption.ALL:
            stmt = stmt.where(
                    Concept.author.like(f'%{author}%'),
                    Concept.title.like(f'%{title}%'),
                    Concept.updated_at > not_before,
                    Concept.updated_at < not_after
                    )
        elif fuzzy == FuzzyOption.AUTHOR:
            stmt = stmt.where(
                    Concept.author.like(f'%{author}%'),
                    Concept.title == title,
                    Concept.updated_at > not_before,
                    Concept.updated_at < not_after
                    )
        elif fuzzy == FuzzyOption.TITLE:
            stmt = stmt.where(
                    Concept.author == author,
                    Concept.title.like(f'%{title}%'),
                    Concept.updated_at > not_before,
                    Concept.updated_at < not_after
                    )
        else:
            stmt = stmt.where(
                    Concept.author == author,
                    Concept.title == title,
                    Concept.updated_at > not_before,
                    Concept.updated_at < not_after
                    )
        return stmt

    @staticmethod
    def find_child_ideas(identifier: str, depth: int) -> Select:
        """Builds a selection statement to find the child ideas
        Arguments:
            identifier: [str] id of the concep to find children for
            depth: [int] number of generations to cap at
        Returns:
            [Select] the selection statement
        """
        steps_cte = select(
                ConceptLink.descendant,
                ConceptLink.ancestor,
                literal(1).label('depth'),
                ) \
            .where(ConceptLink.ancestor == identifier) \
            .cte(recursive=True)
        recursive_query = steps_cte.union_all(
                select(
                    ConceptLink.descendant,
                    ConceptLink.ancestor,
                    steps_cte.c.depth + 1,
                    ).where(ConceptLink.ancestor == steps_cte.c.descendant)
                )
        return select(
                recursive_query.c.ancestor,
                recursive_query.c.descendant,
                steps_cte.c.depth
                ) \
            .where(recursive_query.c.depth <= depth) \
            .order_by(recursive_query.c.depth)

    @staticmethod
    def find_parent_ideas(identifier: str, depth: int) -> Select:
        """Builds a selection statement to find the parent ideas
        Arguments:
            identifier: [str] id of the concept to find parents for
            depth: [int] number of generations to cap at
        Returns:
            [Select] the selection statement
        """
        steps_cte = select(
                    ConceptLink.descendant,
                    ConceptLink.ancestor,
                    literal(1).label('depth')
                ) \
            .where(ConceptLink.descendant == identifier) \
            .cte(recursive=True)
        recursive_query = steps_cte.union_all(
                select(
                    ConceptLink.descendant,
                    ConceptLink.ancestor,
                    steps_cte.c.depth + 1
                    ).where(ConceptLink.descendant == steps_cte.c.ancestor)
                )
        return select(
                recursive_query.c.ancestor,
                recursive_query.c.descendant,
                steps_cte.c.depth
                ) \
            .where(recursive_query.c.depth <= depth) \
            .order_by(recursive_query.c.depth)
