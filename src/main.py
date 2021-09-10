# -*- coding: utf-8 -*- 
# !/usr/bin/env python3 

# IMPORTS
import random
import string

from flask_basic_roles import BasicRoleAuth
from cryptography.fernet import Fernet
from pymongo import MongoClient
from flask import redirect
from flask import request
from flask import Flask

# USER DB CONFIG
USER_MONGO_URI = ""
USER_DATABASE_NAME = ""
USER_COLLECTION_NAME = ""

# LICENSE DB CONFIG
LICENSE_MONGO_URI = ""
LICENSE_DATABASE_NAME = ""
LICENSE_COLLECTION_NAME = ""

# INSTANCES
app = Flask(__name__)
auth = BasicRoleAuth(user_file="roles.txt")

# CONNECT TO DATABASE
cluster = MongoClient(USER_MONGO_URI)
database = cluster[USER_DATABASE_NAME][USER_COLLECTION_NAME]

# CONNECT TO LICENSE DATABASE
cluster_2 = MongoClient(LICENSE_MONGO_URI)
license_database = cluster_2[LICENSE_DATABASE_NAME][LICENSE_COLLECTION_NAME]

# GET KEY
with open("key.txt", "rb") as file:
    key = file.read()


# RESPONSES
def failure():
    """
    Generate a code to represent
    a failure status
    """

    code = random.randint(100000, 999999)

    # Satisfy Condition
    while code % 16 != 0:
        code = random.randint(100000, 999999)

    # Encode to Bytes
    response = str(code).encode()

    # Encrypt
    hash = Fernet(key)
    response = hash.encrypt(response)

    # Response
    return response.decode("utf-8")


def success():
    """
    Generate a code to represent
    a success status
    """

    code = random.randint(100000, 999999)

    # Satisfy Condition
    while code % 42 != 0:
        code = random.randint(100000, 999999)

    # Encode to Bytes
    response = str(code).encode()

    # Encrypt
    hash = Fernet(key)
    response = hash.encrypt(response)

    # Response
    return response.decode("utf-8")


# ENCRYPTION
def encrypt_status(string: str):
    """
    Hash an API response with
    Fernet
    """

    # Encode to Bytes
    response = string.encode()

    # Encrypt
    hash = Fernet(key)
    response = hash.encrypt(response)

    # Response
    return response.decode("utf-8")


# -- CLIENT ENDPOINTS --
@app.route("/view/<string:username>+<string:password>", methods=["GET"])
@auth.require(users=("CLIENT_KEY", "ADMIN_KEY"))
def view_hwid(username, password):
    """
    Get a user's HWID given a user +
    password
    """

    if request.method == "GET":
        # Search Database
        res = database.find({"username": username, "password": password})

        # Dummy Invalid Response
        query = {"username": None, "password": None}

        # Iterate over 'res' Response
        for query in res:
            query = query

        # Return encrypted HWID
        if query["username"] == username and query["password"] == password:
            return {"status": encrypt_status(query["hwid"])}

        return {"status": failure()}


@app.route("/login/<string:username>+<string:password>+<string:id>", methods=["POST"])
@auth.require(users=("CLIENT_KEY", "ADMIN_KEY"))
def auth_user(username, password, id):
    """
    Check if a user is valid, given user
    information

    Note: the 'id' parameter refers to the
    HWID on the client-side
    """

    if request.method == "POST":
        # Check Login Information
        # Search Database
        res = database.find({"username": username, "password": password})

        # Dummy Invalid Response
        query = {"username": None, "password": None}

        # Iterate over 'res' Response
        for query in res:
            query = query

        # If Login is Incorrect
        if query["username"] != username or query["password"] != password:
            return {"status": failure()}

        # If HWID is None
        if query["hwid"] is None:
            database.update_one(
                {"username": username, "password": password},
                {"$set": {"hwid": id}},
            )

            return {"status": success()}

        # Validate HWID if HWID already exists
        if query["hwid"] == id:
            return {"status": success()}

        # Else:
        return {"status": failure()}


# -- ADMIN ENDPOINTS --
@app.route("/reset/<string:username>", methods=["PATCH"])
@auth.require(users=("ADMIN_KEY"))
def reset_hwid(username):
    """
    Reset a user's HWID
    """

    if request.method == "PATCH":
        # Find a Username
        res = database.find({"username": username})

        # Dummy Invalid Response
        query = {"username": None}

        # Iterate over 'res' Response
        for query in res:
            query = query

        # Check if Username is Correct
        if query["username"] == username:
            # Reset HWID and Add +1 to Resets
            database.update_one(
                {"username": username},
                {"$set": {"hwid": None, "resets": (query["resets"] + 1)}},
            )
            return {"status": success()}

        # Else:
        return {"status": failure()}


@app.route("/fetch/<string:username>", methods=["GET"])
@auth.require(users=("ADMIN_KEY"))
def view_login(username):
    """
    View login information for
    a user
    """

    if request.method == "GET":
        # Find a Username
        res = database.find({"username": username})

        # Dummy Invalid Response
        query = {"username": None}

        # Iterate over 'res' Response
        for query in res:
            query = query

        # Check if Username is Correct
        if query["username"] == username:
            # Return Information
            return {
                "username": encrypt_status(query["username"]),
                "password": encrypt_status(query["password"]),
                "resets": encrypt_status(str(query["resets"])),
            }

        # Else:
        return {"status": failure()}


@app.route("/delete/<string:username>", methods=["DELETE"])
@auth.require(users=("ADMIN_KEY"))
def delete_login(username):
    """
    Delete a user's login
    """

    if request.method == "DELETE":
        # Find a Username
        res = database.find({"username": username})

        # Dummy Invalid Response
        query = {"username": None}

        # Iterate over 'res' Response
        for query in res:
            query = query

        # Check if Username is Correct
        if query["username"] == username:
            database.delete_one({"username": username})
            return {"status": success()}

        # Else:
        return {"status": failure()}


@app.route("/generate", methods=["POST"])
@auth.require(users=("ADMIN_KEY"))
def generate():
    """
    Create a license key and
    return it
    """

    if request.method == "POST":
        # Make License Key
        code = "".join(
            random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits
            )
            for _ in range(16)
        )

        # Inset License into DB
        license_database.insert_one({"license": code.upper(), "status": "verified"})

        # Return
        return {"status": encrypt_status(code.upper())}


@app.route(
    "/register/<string:license>+<string:username>+<string:password>", methods=["POST"]
)
@auth.require(users=("ADMIN_KEY"))
def register_user(license, username, password):
    """
    Register a user given a
    username + password
    """

    if request.method == "POST":
        # Check if username already exists
        # Find a Username
        res = database.find({"username": username})

        # Dummy Invalid Response
        query = {"username": None}

        # Iterate over 'res' Response
        for query in res:
            query = query

        # Check if Username Already Exists
        if query["username"] == username:
            return {"error": encrypt_status("This username already exists.")}

        # Check License
        results = license_database.find({"license": license.upper()})

        # Dummy Invalid Response
        document = {"license": None, "status": None}

        # Iterate over 'results' Response
        for document in results:
            document = document

        if document["license"] is None:
            return {"error": encrypt_status("The provided license is invalid.")}

        # Else:
        license_database.delete_one({"license": license})
        database.insert_one(
            {
                "username": username,
                "password": password,
                "hwid": None,
		"resets": 0,
		"discord_id": 0
            }
        )
        return {"status": success()}


if __name__ == "__main__":
    # Note: Adjust the host kwarg in the case of hosting issues.
    app.run(host="0.0.0.0", port=8080)
