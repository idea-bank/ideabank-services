"""
    :module name: accounts
    :module summary: Unified service provider for account information
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging

from sqlalchemy import select, insert
from sqlalchemy.sql.expression import Select, Insert

from .querydb import QueryService
from .s3crud import S3Crud
from ..models.schema import Accounts

LOGGER = logging.getLogger(__name__)


class AccountsDataService(QueryService, S3Crud):
    """Provider for account information."""

    @staticmethod
    def create_account(username, hashed_password, salt_value) -> Insert:
        """Builds an insertion statement to create a new user account
        Arguments:
            username: [str] the display of the new account to create
            hashed_password: [str] the sha256 hash of the given password
            salt_value: [str] the random string used during hashing
        Returns:
            [Insert] a SQLAlchemy Insert statement to create the account
        """
        LOGGER.info("Built query to create a new account")
        return insert(Accounts) \
            .values(
                    display_name=username,
                    password_hash=hashed_password,
                    salt_value=salt_value
                    ) \
            .returning(Accounts.display_name)

    @staticmethod
    def fetch_authentication_information(display_name) -> Select:
        """Builds a selection statement to query a user's credentials
        Arguments:
            display_name: [str] the display name of the account to query for
        Returns:
            [Select] a SQLAlchemy Select statement
        """
        LOGGER.info("Built query to obtain authentication information")
        return select(
                Accounts.password_hash,
                Accounts.salt_value
                ) \
            .where(Accounts.display_name == display_name)
