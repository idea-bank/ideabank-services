"""
    :module_name: utils
    :module_summary: Utilities for the create web2 user service
    :module_name: Nathan Mendoza (nathancm@uci.edu)
"""

from dataclasses import dataclass
from uuid import uuid4
from hashlib import sha256
from secrets import token_hex

@dataclass
class NewUser:
    """
        Dataclass representing a new user account to create
    """
    uuid: str
    display_name: str
    authkeys: dict

    def __init__(self, name, **keys):
        self.uuid = uuid4()
        self.display_name = name
        self.authkeys = keys

@dataclass
class Web2Key:
    """
        Dataclass representing the credentials of a new web2 user
    """
    email: str
    pass_hash: str
    salt: str

    def __init__(self, raw_user, raw_pass):
        self.email = raw_user
        self.pass_hash, self.salt = self.__mix_it_up(raw_pass)

    def __mix_it_up(self, thing_to_mix: str) -> (str, str):
        """
            Helper method to ensure password is not stored as plain text
            :arg thing_to_mix: the password to scramble
            :arg type: str
            :returns: hash and salt used
            :rtype: (str, str)
        """
        user_salt = token_hex()
        user_hash = sha256(f'{thing_to_mix}{user_salt}'.encode('utf-8')).hexdigest()
        return user_hash, user_salt
