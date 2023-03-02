"""
    :module_name: function
    :module_summary: main function execution logic
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

from decode import InputDecoder
from record import IdeaBankUser
from utils import NewUser, Web2Key

def handler(event, context): #pylint-disable=unused-argument
    key = Web2Key('some@email.com', 'supersecretpassword')
    user = NewUser('afunnyname', **{'web2': key})
    tbl = IdeaBankUser()
    tbl.create_user(user)
