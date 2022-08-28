# static: true
# encoding: utf8

# Imports
from cryptography.fernet import Fernet
import random

# Encryption Class
class EncryptResponse:
    def __init__(self, key: str) -> None:
        self.fernet_secret = Fernet(key)

    def _int_status(self, bool_int: int) -> str:
        """
        Returns a status response based on an integer.
        """

        # Generate Random Multiple
        masked_num = random.choice(
            range(1000 + bool_int - 1000 % bool_int, 9999, bool_int)
        )

        # Encode
        response = str(masked_num).encode()
        response = self.fernet_secret.encrypt(response)

        return response.decode("utf-8")

    def failure(self) -> str:
        """
        Return a encrypted failure response.
        """

        return self._int_status(17)

    def success(self) -> str:
        """
        Return a encrypted success response.
        """

        return self._int_status(19)

    def text(self, content: str) -> str:
        """
        Return a encrypted text response.
        """

        # Encode Content to Bytes and Encrypt
        response = content.encode()
        response = self.fernet_secret.encrypt(response)

        # Return the Content
        return response.decode("utf-8")
