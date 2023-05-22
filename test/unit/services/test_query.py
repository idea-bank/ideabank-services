"""Tests for the query service"""

import pytest
from unittest.mock import patch

from ideabank_webapi.services import QueryService
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, text


@patch.object(QueryService, 'CONNINFO', 'sqlite:///:memory:')
class TestQueryService:
    def setup_method(self):
        self.qs = QueryService()

    def test_connection_string_mocked(self):
        assert self.qs.CONNINFO == 'sqlite:///:memory:'

    def test_new_service_instance_has_no_results_and_no_queued_queries(self):
        assert self.qs.results is None
        assert len(self.qs._query_buffer) == 0

    def test_beginning_a_transaction_yields_a_session(self):
        with self.qs.begin_transaction() as session:
            assert isinstance(session, Session)

    def test_execution_with_no_queued_queries_throws_error(self):
        with pytest.raises(IndexError):
            with self.qs.begin_transaction() as session:
                self.qs.exec_next(session)

    def test_query_queue_size_increases_when_query_added(self):
        for i in range(1, 11):
            stmt = select(i)
            self.qs.add_query(stmt)
            assert len(self.qs._query_buffer) == i

    @pytest.mark.parametrize("i", range(1, 11))
    def test_results_of_successful_query_are_executable(self, i):
        stmt = select(i)
        self.qs.add_query(stmt)
        with self.qs.begin_transaction() as session:
            self.qs.exec_next(session)
            assert self.qs.results.scalar() == i

    @pytest.mark.xfail(raises=SQLAlchemyError)
    def test_error_is_propogated_after_transaction_cleaned_up(self):
        stmt = text('SELECT * FROM notatable')
        self.qs.add_query(stmt)
        with self.qs.begin_transaction() as session:
            self.qs.exec_next(session)
