"""
    :module_name: decode
    :module_summary: tools for extracting and decoding input received by the service
    :module_author: Nathan Mendoza (nathancm@uci.edu)
"""

import base64
import binascii

from exceptions import MissingInformationException, MalformedDataException

class InputDecoder:
    """
        A class that helps decode event data
    """
    def __init__(self, event_data: dict):
        self._input = event_data

    def extract(self) -> dict:
        """
            Extract the required data from the event
            :returns: expected information
            :rtype: dict
            :raises: MissingInformationException if expected information is missing
        """
        try:
            return {
                    "displayName": self._input['displayName'],
                    "credentialString": self._input['credentials']
                    }
        except KeyError as err:
            raise MissingInformationException(f"Missing required information: `{err}`") from err

    def decode(self, credential_string):
        """
            Decode the given credential string as a user/pass combination
            :arg credential_string: base64 encoded string with format `user:pass`
            :returns: mapping of decoded user / pass combinatino
            :rtype: dict
            :raises: MalformedDataException if decode fails or user/pass combination cannot be deciphered
        """
        try:
            decoded = base64.b64decode(credential_string.encode('utf-8')).decode('utf-8')
            user_email, pass_phrase = decoded.split(':', 1)
            return {
                    'user_email': user_email,
                    'user_pass': pass_phrase
                    }
        except (ValueError, binascii.Error) as err:
            raise MalformedDataException("Could not decipher credential string") from err
