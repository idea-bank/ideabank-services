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
        self._display_name = None
        self._credential_string = None

    def extract(self):
        """
            Extract the required data from the event
            :returns: updated input decoder object
            :rtype: self
            :raises: MissingInformationException if expected information is missing
        """
        try:
            self._display_name = self._input['displayName']
            self._credential_string = self._input['credentials']
            return self
        except KeyError as err:
            raise MissingInformationException(f"Missing required information: `{err}`") from err

    def decode(self):
        """
            Decode the given credential string as a user/pass combination
            :arg credential_string: base64 encoded string with format `user:pass`
            :returns: mapping of decoded user / pass combinatino
            :rtype: dict
            :raises: MalformedDataException if decode fails or credential string is undecipherable
        """
        if not self._display_name or not self._credential_string:
            raise MissingInformationException(
                    "Cannot decode unknown credentials. Perhaps you forgot to call extract()?"
                )
        try:
            decoded = base64.b64decode(self._credential_string.encode('utf-8')).decode('utf-8')
            user_email, pass_phrase = decoded.split(':', 1)
            return {
                    'display_name': self._display_name,
                    'user_email': user_email,
                    'user_pass': pass_phrase
                    }
        except (ValueError, binascii.Error) as err:
            raise MalformedDataException("Could not decipher credential string") from err
