"""
    :module_name: utils
    :module_summary: Utilities for the create web2 user service
    :module_name: Nathan Mendoza (nathancm@uci.edu)
"""

from dataclasses import dataclass
from uuid import uuid4

@dataclass
class UserProfile:
    real_name: str
    age: int
    bio: str
    avatar: str

    @classmethod
    def blank(cls):
        return cls(
                real_name=None,
                age=None,
                bio=None,
                avatar=None
                )

@dataclass
class NewUser:
    uuid: str
    display_name: str
    profile: UserProfile
    authkeys: dict

    def __init__(self, name, **keys):
        self.uuid = uuid4()
        self.display_name = name
        self.profile = UserProfile.blank()
        authkeys = keys

@dataclass
class Web2Key:
    email: str
    pass_hash: str
    salt: str
