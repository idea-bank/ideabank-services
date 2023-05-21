"""Tests for the database schema declarative models"""

import secrets
import string
import random

from ideabank_webapi.models import IdeaBankSchema
from ideabank_webapi.models import Accounts
from ideabank_webapi.models import Concept
from ideabank_webapi.models import ConceptLink

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

import pytest


@pytest.fixture
def a_password():
    return ''.join(random.choices(
            list(
                string.ascii_lowercase + string.ascii_uppercase + string.digits
                ),
            k=32
            ))


class TestIdeaBankSchema:

    def setup_method(self):
        self.engine = create_engine('sqlite:///:memory:', echo=True)
        with Session(self.engine):
            IdeaBankSchema.metadata.create_all(self.engine)

    @pytest.mark.parametrize("username", ['user1', 'user2', 'user3'])
    def test_user_record_creation(self, username, a_password):
        with Session(self.engine) as session:
            stmt = insert(Accounts).values(
                    {
                        'display_name': username,
                        'password_hash': a_password,
                        'salt_value': secrets.token_hex()
                        }
                    )
            session.execute(stmt)
            session.commit()

    @pytest.mark.parametrize("username", ['user1', 'user2', 'user3'])
    def test_duplicate_user_cannot_be_created(self, username, a_password):
        with pytest.raises(IntegrityError):
            with Session(self.engine) as session:
                stmt = insert(Accounts).values(
                        {
                            'display_name': username,
                            'password_hash': a_password,
                            'salt_value': secrets.token_hex()
                            }
                        )
                session.execute(stmt)
                session.execute(stmt)

    @pytest.mark.parametrize("username, idea", [
        ('user1', 'idea1'),
        ('user2', 'idea2'),
        ('user3', 'idea3')
        ]
    )
    def test_concept_creation(self, username, idea, a_password):
        with Session(self.engine) as session:
            stmt = insert(Accounts).values(
                        {
                            'display_name': username,
                            'password_hash': a_password,
                            'salt_value': secrets.token_hex()
                            }
                        )
            session.execute(stmt)
            stmt = insert(Concept).values(
                    {
                        'author': username,
                        'title': idea,
                        'description': '...',
                        'diagram': '{}'
                        }
                    )
            session.execute(stmt)

    @pytest.mark.parametrize("username, idea", [
        ('user1', 'idea1'),
        ('user2', 'idea2'),
        ('user3', 'idea3')
        ]
    )
    def test_user_cannot_have_duplicate_titles(self, username, idea, a_password):
        with pytest.raises(IntegrityError):
            with Session(self.engine) as session:
                stmt = insert(Accounts).values(
                            {
                                'display_name': username,
                                'password_hash': a_password,
                                'salt_value': secrets.token_hex()
                                }
                            )
                session.execute(stmt)
                stmt = insert(Concept).values(
                        {
                            'author': username,
                            'title': idea,
                            'description': '...',
                            'diagram': '{}'
                            }
                        )
                session.execute(stmt)
                session.execute(stmt)

    def test_linking_of_ideas(self, a_password):
        with Session(self.engine) as session:
            for username in ['user1', 'user2']:
                stmt = insert(Accounts).values(
                            {
                                'display_name': username,
                                'password_hash': a_password,
                                'salt_value': secrets.token_hex()
                                }
                            )
                session.execute(stmt)

                for idea in ['idea1', 'idea2']:
                    stmt = insert(Concept).values(
                            {
                                'author': username,
                                'title': idea,
                                'description': '...',
                                'diagram': '{}'
                                }
                            )
                    session.execute(stmt)

            for start, end in [('user1/idea1', 'user2/idea1'), ('user2/idea2', 'user1/idea1')]:
                stmt = insert(ConceptLink).values({
                        'ancestor': start,
                        'descendant': end
                        })
                session.execute(stmt)
