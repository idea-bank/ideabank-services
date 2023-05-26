"""Tests for the query service"""

import pytest
from unittest.mock import patch

from ideabank_webapi.exceptions import NoQueryToRunError, NoSessionToQueryOnError
from ideabank_webapi.services import QueryService
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, text, create_engine


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
class TestQueryService:
    def setup_method(self):
        self.qs = QueryService()

    def test_new_service_instance_has_no_results_and_no_queued_queries(self):
        assert self.qs.results is None
        assert len(self.qs._query_buffer) == 0
        assert self.qs._session is None

    def test_beginning_a_transaction_defines_a_session(self):
        with self.qs:
            assert self.qs._session is not None
        assert self.qs._session is None

    def test_execution_with_no_queued_queries_throws_error(self):
        with pytest.raises(NoQueryToRunError):
            with self.qs as t:
                t.exec_next()

    def test_attempting_to_run_queries_without_session_throws_error(self):
        with pytest.raises(NoSessionToQueryOnError):
            self.qs.add_query(select(1))
            self.qs.exec_next()

    def test_query_queue_size_increases_when_query_added(self):
        for i in range(1, 11):
            stmt = select(i)
            self.qs.add_query(stmt)
            assert len(self.qs._query_buffer) == i

    @pytest.mark.parametrize("i", range(1, 11))
    def test_results_of_successful_query_are_executable(self, i):
        stmt = select(i)
        self.qs.add_query(stmt)
        with self.qs as t:
            t.exec_next()
            assert t.results.scalar() == i

    @pytest.mark.xfail(raises=SQLAlchemyError)
    def test_error_is_propogated_after_transaction_cleaned_up(self):
        stmt = text('SELECT * FROM notatable')
        self.qs.add_query(stmt)
        with self.qs as t:
            t.exec_next()

    @pytest.mark.parametrize("i", range(1, 11))
    def test_execute_next_reduces_query_buffer_size(self, i):
        stmt = select(i)
        self.qs.add_query(stmt)
        self.qs.add_query(stmt)
        with self.qs as t:
            t.exec_next()
            assert len(self.qs._query_buffer) == 1
            assert t.results.scalar() == i
