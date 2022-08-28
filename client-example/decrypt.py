# static: true
# encoding: utf8

# Imports
from cryptography.fernet import Fernet
from typing import Union

# Decryption Class
class DecryptResponse:
    def __init__(self, key: str) -> None:
        self.secret = key

    def decode_response(self, response: str) -> str:
        """
        Parse an encrypted API response to a string.
        """

        response_as_bytes = str.encode(response)
        ckey = Fernet(self.secret)

        decrypted_bytes = ckey.decrypt(response_as_bytes)
        return decrypted_bytes.decode("utf-8")

    def decode_json(self, response: dict) -> dict:
        """
        Parse an encrypted API response to a dictionary.
        """

        return {key: self.decode_response(val) for key, val in response.items()}

    def parse_to_bool(self, response: str) -> Union[bool, None]:
        """
        Parse an encrypted API response to a boolean.
        """

        decrypt = self.decode_response(response)
        to_int = int(decrypt)

        if to_int % 17 == 0:
            return False
        elif to_int % 19 == 0:
            return True
