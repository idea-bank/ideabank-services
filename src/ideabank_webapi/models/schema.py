"""
    :module name: schema
    :module summary: Declarative db schema using SQLAlchemy
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import datetime

from sqlalchemy.orm import DeclarativeBase, column_property
from sqlalchemy import Column, String, DateTime, JSON


class IdeaBankSchema(DeclarativeBase):  # pylint:disable=too-few-public-methods
    """Base schema object for the idea bank data schema"""


def _derive_preferred_name(context):
    """Gets the default preferred name base on current display name"""
    return context.get_current_parameters()['display_name']


def _default_bio_placeholder(context):
    """Gets the default bio based on current display name"""
    current_username = context.get_current_parameters()['display_name']
    return f'{current_username} hasn\'t added a bio.'


class Accounts(IdeaBankSchema):  # pylint:disable=too-few-public-methods
    """Models a row in the Accounts
    Attributes:
        display_name: the unique identifier for the account
        preferred_name: the name the account displays throughout the app
        biography: the backstory of this account
        password_hash: the hash password required to access this account
        salt_value: the unique salting value used by this account
        created_at: the timestamp of the sign up time
        updated_at: the timestamp of the last time the account was modified
    """
    __tablename__ = 'accounts'
    display_name = Column(String(64), primary_key=True)
    preferred_name = Column(String(255), default=_derive_preferred_name)
    biography = Column(String, default=_default_bio_placeholder)
    password_hash = Column(String(64))
    salt_value = Column(String(64))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
            DateTime,
            default=datetime.datetime.utcnow,
            onupdate=datetime.datetime.utcnow
            )


class Concept(IdeaBankSchema):  # pylint:disable=too-few-public-methods
    """Models a row in the concepts table
    Attributes:
        title: the title of this concept
        author: the display name of the creator of this concept
        description: a textual description of the concepts
        diagram: a JSON model of the component graph making this concept
        created_at: the timestamp of the create time of this concept
        updated_at: the timestamp of the last updated time of this concept
        identifier: [derived] a unique string identifying a given concept
    """
    __tablename__ = 'concepts'
    title = Column(String(128), primary_key=True)
    author = Column(String(64), primary_key=True)
    description = Column(String)
    diagram = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
            DateTime,
            default=datetime.datetime.utcnow,
            onupdate=datetime.datetime.utcnow
            )
    identifier = column_property(author + "/" + title)


class ConceptLink(IdeaBankSchema):  # pylint:disable=too-few-public-methods
    """Models a row in the concept links table
    Attributes:
        ancestor: the unique identifying string of the ancestor concept
        descendant: the unique identifying string of the descendant concept
    """
    __tablename__ = 'concept_links'
    ancestor = Column(String(255), primary_key=True)
    descendant = Column(String(255), primary_key=True)
