"""
    :module name: engage
    :module summary: Service provider for application engagement
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
from typing import Optional

from sqlalchemy import select, insert, delete
from sqlalchemy.sql.expression import Select, Insert, Delete

from .querydb import QueryService
from ..models.schema import Likes, Follows, Comments

# pylint:disable=singleton-comparison
LOGGER = logging.getLogger(__name__)


class EngagementDataService(QueryService):
    """Provider for user engagement"""

    @staticmethod
    def insert_liking(account_liking: str, concept_liked: str) -> Insert:
        """Builds an insertion statement to record the action of liking an idea
        Arguments:
            account_liking: [str] the display of the user liking something
            concept_liked: [str] the identifying string of the concept being liked
        Returns:
            [Insert] An sqlalchemy insertion statement to create the liked record
        """
        LOGGER.info("Built query to like an idea")
        return insert(Likes) \
            .values(
                display_name=account_liking,
                concept_id=concept_liked
                    ) \
            .returning(
                Likes.display_name,
                Likes.concept_id
                    )

    @staticmethod
    def revoke_liking(account_unliking: str, concept_unliked: str) -> Delete:
        """Builds a deletion statement to record the action of unliking an idea
        Arguments:
            account_unliking: [str] the display name of the user unliking an idea
            concept_unliked: [str] the identifying string of the unliked idea
        Returns:
            [Delete] An sqlalchemy deletion statement to remove the like record
        """
        LOGGER.info("Built query to unlike an idea")
        return delete(Likes) \
            .where(
                    Likes.display_name == account_unliking,
                    Likes.concept_id == concept_unliked
                    )

    @staticmethod
    def check_liking(account: str, concept: str) -> Select:
        """Builds a selection statement to check if a record of account liking concept exists
        Arguments:
            account: [str] the display name to check for
            concept: [str] the concept identifier to check for
        Returns:
            [Select] An sqlalchemy selection statement to check for the record
        """
        LOGGER.info("Built query to check if an idea is liked by a particular user")
        return select(Likes).where(
                Likes.display_name == account,
                Likes.concept_id == concept
                )

    @staticmethod
    def insert_following(follower: str, followee: str) -> Insert:
        """Builds an insertion statement to record the action of following another user
        Arguments:
            follower: [str] the account wanting to follow another user
            followee: [str] the account being followed by another user
        Returns:
            [Insert] A sqlalchemy insertion statement to record the following event
        """
        LOGGER.info("Built query to follow another user")
        return insert(Follows) \
            .values(
                    follower=follower,
                    followee=followee
                    ) \
            .returning(
                    Follows.follower,
                    Follows.followee
                    )

    @staticmethod
    def revoke_following(follower: str, followee: str) -> Delete:
        """Builds a deletion statement to record the event of an unfollowing
        Arguments:
            follower: [str] the account wanting to unfollow another user
            followee: [str] the account being unfollowed by anothe user
        Returns:
            [Delete] A sqlalchemy deletion statement to record the unfollowing event
        """
        LOGGER.info("Built query to unfollow another user")
        return delete(Follows).where(
                Follows.followee == followee,
                Follows.follower == follower
                )

    @staticmethod
    def check_following(follower: str, followee: str) -> Select:
        """Builds a selection statement to check if a user follows another user
        Arguments:
            follower: [str] the account following another user
            followee: [str] the account being followed by another user
        Returns:
            [Select] an sqlalchemy selection statement to find the following record
        """
        LOGGER.info("Built query to check if a user is following another user")
        return select(Follows) \
            .where(
                    Follows.follower == follower,
                    Follows.followee == followee
                    )

    @staticmethod
    def create_comment(
            author: str,
            concept: str,
            contents: str,
            response_to: Optional[int] = None
            ) -> Insert:
        """Builds an insertion statement to create a new comment
        Arguments:
            author: [str] the display name of the user creating this comment
            concept: [str] the identifier string of the concept being commented on
            contents: [str] the contents of the comment
            response_to: [int] the id of the comment this comment responds to (if any)
        Returns:
            A sqlalchemy insertion statement to create the comment
        """
        LOGGER.info("Built query to create a new comment")
        return insert(Comments) \
            .values(
                    comment_on=concept,
                    comment_by=author,
                    free_text=contents,
                    parent=response_to
                    ) \
            .returning(
                    Comments.comment_id
                    )

    @staticmethod
    def comments_on(concept_id: str, response_to: str = None) -> Select:
        """Builds a selection statement to gather comments of a given thread on a given idea
        Arguments:
            concept_id: [str] the string identifier of the concept being commented on
            response_to: [int] the initial comment thread to gather for
        Returns:
            A sqlalchemy selection statement to gather thread comments
        """
        LOGGER.info("Built query to find comments part of a given thread")
        return select(Comments.comment_id, Comments.comment_by, Comments.free_text) \
            .where(Comments.comment_on == concept_id, Comments.parent == response_to) \
            .order_by(Comments.created_at)
