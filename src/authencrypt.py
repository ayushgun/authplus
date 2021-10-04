# -*- coding: utf-8 -*-
# !/usr/bin/env python3

# IMPORTS
import random

from cryptography.fernet import Fernet

# CRYPTOGRAPHY KEY
def find_key():
    """
    Retrieve the Fernet Cryptography
    key from a local file
    """

    with open("key.txt", "rb") as file:
        # Constraint: Single-line file
        return file.read()


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
    hash = Fernet(find_key())
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
    hash = Fernet(find_key())
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
    hash = Fernet(find_key())
    response = hash.encrypt(response)

    # Response
    return response.decode("utf-8")
