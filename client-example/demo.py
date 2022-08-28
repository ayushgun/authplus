# static: true
# encoding: utf8

# Imports
from decrypt import DecryptResponse
from pprint import pprint

import requests

# Client Configuration
API_URL = ""
FERNET_KEY = ""

# Instantiate Decryption Class
decrypt = DecryptResponse(key=FERNET_KEY)

# Sample Credential Data
username = "Foo"
password = "Bar"
hwid = "00000000-0000-0000-0000-0000000000000"

# Login User
req = requests.post(
    f"{API_URL}/login?username={username}&password={password}&hwid={hwid}",
    auth=("CLIENT", "CLIENT_PASSWORD"),  # Set in your config
)
pprint(decrypt.decode_json(req.json()))


# Register User
req = requests.post(
    f"{API_URL}/register?username={username}&password={password}&license_key=X99HPTKDQZLFAWJZ",
    auth=("ADMIN", "ADMIN_PASSWORD"),  # Set in your config
)
pprint(decrypt.decode_json(req.json()))


# Fetch User
req = requests.get(
    f"{API_URL}/account?username={username}",
    auth=("ADMIN", "ADMIN_PASSWORD"),  # Set in your config
)
pprint(decrypt.decode_json(req.json()))


# Delete User
req = requests.delete(
    f"{API_URL}/delete?username={username}",
    auth=("ADMIN", "ADMIN_PASSWORD"),  # Set in your config
)
pprint(decrypt.decode_json(req.json()))


# Reset User's HWID
req = requests.patch(
    f"{API_URL}/hwid?username={username}",
    auth=("ADMIN", "ADMIN_PASSWORD"),  # Set in your config
)
pprint(decrypt.decode_json(req.json()))

# Reset User's Password
req = requests.patch(
    f"{API_URL}/password?username={username}&new_password=0420",
    auth=("ADMIN", "ADMIN_PASSWORD"),  # Set in your config
)
pprint(decrypt.decode_json(req.json()))


# Change User's Profile Note
req = requests.patch(
    f"{API_URL}/note?username={username}&note=Hello+World",
    auth=("ADMIN", "ADMIN_PASSWORD"),  # Set in your config
)
pprint(decrypt.decode_json(req.json()))


# Generate Registration License
req = requests.get(
    f"{API_URL}/license", auth=("ADMIN", "ADMIN_PASSWORD")  # Set in your config
)
pprint(decrypt.decode_json(req.json()))


# Get App Statistics
req = requests.get(
    f"{API_URL}/stats", auth=("ADMIN", "ADMIN_PASSWORD")  # Set in your config
)
pprint(decrypt.decode_json(req.json()))
