"""
    :module name: querydb
    :module summary: Base service class for interacting with application db
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

from contextlib import contextmanager
from typing import Union, Optional

from sqlalchemy import create_engine, URL, Result
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import Select, Update, Delete

from ..config import ServiceConfig


class QueryService:
    """A class wrapping database connection and transactions
    Attributes:
        ENGINE: the db engine used by the service.
        query_buffer: the list of queued queries to execute
        results: results of the last executed query
    """
    CONNINFO = URL.create(
                        drivername="postgresql+psycopg",
                        username=ServiceConfig.DataBase.DBUSER,
                        password=ServiceConfig.DataBase.DBPASS,
                        host=ServiceConfig.DataBase.DBHOST,
                        port=ServiceConfig.DataBase.DBPORT,
                        database=ServiceConfig.DataBase.DBNAME
                        )
    ENGINE = create_engine(CONNINFO)

    def __init__(self):
        self._query_buffer = []
        self._query_results = None

    @contextmanager
    def begin_transaction(self):
        """Provides a SQLAlchemy session to supervise the transaction"""
        try:
            session = Session(self.ENGINE)
            yield session
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

    def add_query(self, query: Union[Select, Update, Delete]) -> None:
        """Adds the given query to the query buffer
        Arguments:
            query: [Select | Update | Delete] a sqlalchemy stmt
        Returns:
            None
        """
        self._query_buffer.append(query)

    def exec_next(self, session: Session) -> None:
        """Use the given session to execute the next query in the buffer
        Arguments:
            session: [Session] session to execute the query with
        Returns:
            None
        Raises:
            IndexError if no next query is queued
        """
        stmt = self._query_buffer.pop(0)
        self._query_results = session.execute(stmt)

    @property
    def results(self) -> Optional[Result]:
        """Return the current value of self._query_results
        Returns:
            [Optional[Result]]: results of the last query successfully run
        """
        return self._query_results
