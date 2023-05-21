"""Tests for the database schema declarative models"""

from ideabank_webapi.models import IdeaBankSchema

from sqlalchemy import create_engine
from sqlalchemy.orm import Session


class TestIdeaBankSchema:
    DB_ENGINE = None

    @classmethod
    def setup_class(cls):
        cls.DB_ENGINE = create_engine('sqlite:///:memory:', echo=True)

    @classmethod
    def teardown_class(cls):
        cls.DB_ENGINE = None

    def test_database_schema_is_creatable(self):
        with Session(self.DB_ENGINE):
            IdeaBankSchema.metadata.create_all(self.DB_ENGINE)
