"""
An example module for decrypting response data from the AuthPlus REST API.
"""

from cryptography.fernet import Fernet


class EncryptedResponse:
    def __init__(self, encrypted_data: dict) -> None:
        self.data = encrypted_data

    def decrypt(self, key: str) -> dict:
        """
        Decrypt response data using the Fernet key.
        """

        decrypted_data = {}
        fernet = Fernet(key)

        # Decrypt encrypted value for all keys in data
        for key, value in self.data.items():
            decrypted_value = fernet.decrypt(str.encode(value))
            decrypted_data[key] = decrypted_value.decode("utf-8")

        return decrypted_data
