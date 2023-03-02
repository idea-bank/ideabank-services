"""
    :module_name: function
    :module_summary: main function execution logic
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

from decode import InputDecoder
from record import IdeaBankUser
from utils import NewUser, Web2Key
from exceptions import MissingInformationException, MalformedDataException

def handler(event, context): #pylint-disable=unused-argument
    new_user_data = InputDecoder(event).extract().decode()
    key = Web2Key(new_user_data['user_email'], new_user_data['user_pass'])
    user = NewUser(new_user_data['display_name'], **{'web2': key})
    table = IdeaBankUser()
    table.create_user(user)
