"""
A comprehensive test suite for the AuthPlus REST API.
"""

import datetime
import os
import pathlib
import unittest

import dotenv
import requests
from responses import EncryptedResponse

# Load .env and declare test suite constants
path = pathlib.Path(__file__).parent.parent.resolve()
dotenv.load_dotenv(f"{path}/configuration/config.env")
URL = os.getenv("api_url")
TODAY = datetime.date.today().strftime("%m/%d/%Y")

# Get authorization data and decryption key from .env
admin_auth = ("ADMIN", os.getenv("admin_password"))
client_auth = ("CLIENT", os.getenv("client_password"))
key = os.getenv("encryption_key")

# Initialize test account data to test and create
test_data = {"username": "demo", "password": "password"}


class TestEndpoints(unittest.TestCase):
    def test_00_root(self) -> None:
        """
        Test the root endpoint for expected behavior.
        """

        # Make request to endpoint
        request = requests.get(URL, timeout=5)

        # Check if redirected to main website
        self.assertEqual(request["status"], "online")

    def test_01_stats(self) -> None:
        """
        Check stats endpoint for expected behavior.
        """

        # Make request to endpoint and store response
        request = requests.get(f"{URL}/stats", timeout=5)
        response = request.json()

        # Check if response contains correct keys
        self.assertIn("license_count", response)
        self.assertIn("order_count", response)
        self.assertIn("user_count", response)

    def test_02_text_embed(self) -> None:
        """
        Test the text embed endpoint for expected behavior.
        """

        # Make request to endpoint and store response
        params = {"title": "demo", "description": "demo", "hex": "ffffff"}
        request = requests.get(f"{URL}/embed/text", params=params, timeout=5)
        html = request.text

        # Check if response HTML contains correct meta tags
        self.assertIn('<meta property="og:title" content="demo" />', html)
        self.assertIn('<meta property="og:description" content="demo" />', html)
        self.assertIn('<meta name="theme-color" content="#ffffff">', html)

    def test_03_image_embed(self) -> None:
        """
        Test the image embed endpoint for expected behavior.
        """

        # Make request to endpoint and store response
        params = {"title": "demo", "url": "https://picsum.photos/100", "hex": "ffffff"}
        request = requests.get(f"{URL}/embed/image", params=params, timeout=5)
        html = request.text

        # Check if response HTML contains correct meta tags
        self.assertIn('<meta property="og:title" content="demo" />', html)
        self.assertIn('<meta name="theme-color" content="#ffffff">', html)
        self.assertIn('<meta name="twitter:card" content="summary_large_image">', html)
        self.assertIn(
            '<meta property="og:image" content="https://picsum.photos/100" />', html
        )

    def test_04_licence_create(self) -> None:
        """
        Test the licence creation endpoint for expected behavior.
        """

        # Make request to endpoint
        request = requests.post(f"{URL}/license/create", auth=admin_auth, timeout=5)

        # Decrypt response data
        response = EncryptedResponse(request.json())
        response = response.decrypt(key)

        # Check if response contains correct keys
        self.assertIn("license", response)

        # Check if response data matches expected behavior
        self.assertEqual(response["date_created"], TODAY)

        # Store data in testing data for later tests
        test_data["license"] = response["license"]

    def test_05_account_create(self) -> None:
        """
        Test the account creation endpoint for expected behavior.
        """

        # Make request to endpoint
        params = {
            "username": test_data["username"],
            "password": test_data["password"],
            "license": test_data["license"],
        }
        request = requests.post(
            f"{URL}/account/create", params=params, auth=admin_auth, timeout=5
        )

        # Decrypt response data
        response = EncryptedResponse(request.json())
        response = response.decrypt(key)

        # Check if response data matches expected behavior
        self.assertEqual(response["status"], "Successfully registered account")

    def test_06_account_login(self) -> None:
        """
        Test the account login endpoint for expected behavior.
        """

        # Make request to endpoint
        params = {
            "username": test_data["username"],
            "password": test_data["password"],
            "hwid": "hwid",
        }
        header = {"user-agent": "TnEQZcdY9hEeBk8r"}
        request = requests.post(
            f"{URL}/account/login",
            params=params,
            auth=client_auth,
            headers=header,
            timeout=5,
        )

        # Decrypt response data
        response = EncryptedResponse(request.json())
        response = response.decrypt(key)

        # Check if response data matches expected behavior
        self.assertEqual(response["status"], "Successfully logged in")

        # Store data in testing data for later tests
        test_data["hwid"] = params["hwid"]

    def test_07_account_hwid(self) -> None:
        """
        Test the account HWID reset endpoint for expected behavior.
        """

        # Make request to endpoint
        params = {"username": test_data["username"]}
        request = requests.patch(
            f"{URL}/account/hwid", params=params, auth=admin_auth, timeout=5
        )

        # Decrypt response data
        response = EncryptedResponse(request.json())
        response = response.decrypt(key)

        # Check if response data matches expected behavior
        self.assertEqual(response["status"], "Successfully reset HWID")

    def test_08_account_password(self) -> None:
        """
        Test the account password reset endpoint for expected behavior.
        """

        # Make request to endpoint
        params = {"username": test_data["username"], "password": "new"}
        request = requests.patch(
            f"{URL}/account/password", params=params, auth=admin_auth, timeout=5
        )

        # Decrypt response data
        response = EncryptedResponse(request.json())
        response = response.decrypt(key)

        # Check if response data matches expected behavior
        self.assertEqual(response["status"], "Successfully changed password")

        # Store data in testing data for later tests
        test_data["password"] = params["password"]

    def test_09_account_note(self) -> None:
        """
        Test the account note change endpoint for expected behavior.
        """

        # Make request to endpoint
        params = {"username": test_data["username"], "note": "data"}
        request = requests.patch(
            f"{URL}/account/note", params=params, auth=admin_auth, timeout=5
        )

        # Decrypt response data
        response = EncryptedResponse(request.json())
        response = response.decrypt(key)

        # Check if response data matches expected behavior
        self.assertEqual(response["status"], "Successfully changed note")

        # Store data in testing data for later tests
        test_data["note"] = params["note"]

    def test_10_account_fetch(self) -> None:
        """
        Test the account fetch endpoint for expected behavior.
        """

        # Make request to endpoint
        params = {"username": test_data["username"]}
        request = requests.get(
            f"{URL}/account/fetch", params=params, auth=admin_auth, timeout=5
        )

        # Decrypt response data
        response = EncryptedResponse(request.json())
        response = response.decrypt(key)

        # Check if response data matches expected behavior
        self.assertEqual(response["username"], test_data["username"])
        self.assertEqual(response["password"], test_data["password"])
        self.assertEqual(response["hwid_resets"], "1")
        self.assertEqual(response["note"], test_data["note"])
        self.assertEqual(response["date_created"], TODAY)

    def test_11_account_delete(self) -> None:
        """
        Test the account deletion endpoint for expected behavior.
        """

        # Make request to endpoint
        params = {"username": test_data["username"]}
        request = requests.delete(
            f"{URL}/account/delete", params=params, auth=admin_auth, timeout=5
        )

        # Decrypt response data
        response = EncryptedResponse(request.json())
        response = response.decrypt(key)

        # Check if response data matches expected behavior
        self.assertEqual(response["status"], "Successfully deleted account")


if __name__ == "__main__":
    unittest.main()
