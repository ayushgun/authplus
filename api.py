# static: true
# encoding: utf8

# FastAPI Imports
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

# SlowAPI Imports
from slowapi.extension import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Other Imports
from motor.motor_asyncio import AsyncIOMotorClient
from starlette_context import middleware, plugins
from encrypt import EncryptResponse
from secrets import compare_digest
from datetime import date

import random
import string
import toml

# Instantiate API
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
security = HTTPBasic()

# Instantiate Ratelimiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Load Config Data
config = toml.load("configuration/api_config.toml")
encrypt = EncryptResponse(config["fernet_key"])

# Load Starlette Middleware
app.add_middleware(
    middleware.ContextMiddleware,  # type: ignore
    plugins=(plugins.ForwardedForPlugin()),  # type: ignore
)

# -*- Startup Functions -*-
async def _open_db() -> None:
    # Connect to database
    app.state.__db = AsyncIOMotorClient(
        config["mongo_uri"], serverSelectionTimeoutMS=5000
    )

    # Load DB collections
    app.state.users = app.state.__db["customers"]["users"]
    app.state.licenses = app.state.__db["customers"]["licenses"]


async def _close_db() -> None:
    app.state.__db.close()


app.add_event_handler("startup", _open_db)
app.add_event_handler("shutdown", _close_db)


# -*- License Management -*-
async def create_license() -> tuple:
    """
    Generate a license key to allow for user registration.
    """

    # Generate key
    license_key = "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
    creation_time = date.today().strftime("%m/%d/%Y")

    # Add to database
    await app.state.licenses.insert_one(
        {"license": license_key, "date_created": creation_time}
    )
    return (license_key, creation_time)


# -*- Authorization Checks -*-
def _check_admin(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """
    Check if the credentials match admin credentials.
    """

    # Check username and password
    correct_user = compare_digest(credentials.username, config["admin"]["username"])
    correct_pass = compare_digest(credentials.password, config["admin"]["password"])

    # Raise error if incorrect credentials
    if not (correct_user and correct_pass):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return True


def _check_client(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """
    Check if the credentials match client credentials.
    """

    # Check username and password
    correct_user = compare_digest(credentials.username, config["client"]["username"])
    correct_pass = compare_digest(credentials.password, config["client"]["password"])

    # Raise error if incorrect credentials
    if not (correct_user and correct_pass):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return True


# -*- Public API Endpoints -*-
@app.get("/", include_in_schema=False)
async def root() -> str:
    """
    [Public]: Displays connection information.
    """

    return "Self-hosted API is online & ready."


# -*- Client API Endpoints -*-
@app.post("/login", dependencies=[Depends(_check_client)])
@limiter.limit("5/minute")
async def login_user(request: Request, username: str, password: str, hwid: str) -> dict:
    """
    [Client]: Validate a user's login.
    """

    # Find account
    find = await app.state.users.find_one({"username": username, "password": password})

    # Check if account not found
    if not find:
        return {"status": encrypt.failure()}

    # Check if hardware ID is present
    if not find["hardware_id"]:
        await app.state.users.update_one(
            {"username": username, "password": password},
            {"$set": {"hardware_id": hwid}},
        )

    elif not compare_digest(find["hardware_id"], hwid):
        # Return error if hardware ID is different
        return {"status": encrypt.failure()}

    return {"status": encrypt.success()}


# -*- Admin API Endpoints -*-
@app.get("/docs", dependencies=[Depends(_check_admin)], include_in_schema=False)
async def get_documentation() -> HTMLResponse:
    """
    [Admin]: Display dynamically generated API documentation.
    """

    return get_redoc_html(openapi_url="/oapi.json", title="docs")


@app.get("/oapi.json", dependencies=[Depends(_check_admin)], include_in_schema=False)
async def openapi() -> dict:
    """
    [Admin]: Display OpenAPI information.
    """

    return get_openapi(title="AuthPlus", version="5.0.0", routes=app.routes)


@app.post("/register", dependencies=[Depends(_check_admin)])
@limiter.limit("5/minute")
async def register_user(
    request: Request, username: str, password: str, license_key: str
) -> dict:
    """
    [Admin]: Register a user with a license key.
    """

    # Find profile
    exists = await app.state.users.find_one({"username": username})

    # Return error if username exists
    if exists:
        return {"status": encrypt.text("This username already exists.")}

    # Check license key
    license_key = license_key.upper()
    license_exists = await app.state.licenses.find_one({"license": license_key})

    # Return error if license is invalid
    if not license_exists:
        return {"status": encrypt.text("Invalid license.")}

    # Create account if checkpoints are valid
    await app.state.licenses.delete_one({"license": license_key})
    await app.state.users.insert_one(
        {
            "username": username,
            "password": password,
            "hardware_id": "",
            "hwid_resets": 0,
            "note": "",
            "date_created": date.today().strftime("%m/%d/%Y"),
        }
    )

    return {"status": encrypt.success()}


@app.get("/account", dependencies=[Depends(_check_admin)])
@limiter.limit("3/minute")
async def fetch_user(request: Request, username: str) -> dict:
    # sourcery skip: assign-if-exp, reintroduce-else, swap-if-expression
    """
    [Admin]: Fetch user account data from a username ID.
    """

    # Find username
    find = await app.state.users.find_one({"username": username})

    # Check if account not found
    if not find:
        return {"status": encrypt.failure()}

    # Return account data as JSON
    return {
        "username": encrypt.text(find["username"]),
        "password": encrypt.text(find["password"]),
        "hwid_resets": encrypt.text(str(find["hwid_resets"])),
        "note": encrypt.text(find["note"]),
        "date_created": encrypt.text(find["date_created"]),
    }


@app.delete("/delete", dependencies=[Depends(_check_admin)])
@limiter.limit("3/minute")
async def delete_user(request: Request, username: str) -> dict:
    """
    [Admin]: Delete a specific user account.
    """

    # Find profile
    exists = await app.state.users.find_one({"username": username})

    # Return error if account does not exist
    if not exists:
        return {"status": encrypt.text("Unable to locate that account.")}

    # Delete from database
    await app.state.users.delete_one({"username": username})
    return {"status": encrypt.success()}


@app.patch("/hwid", dependencies=[Depends(_check_admin)])
@limiter.limit("3/minute")
async def reset_hardware_id(request: Request, username: str) -> dict:
    """
    [Admin]: Reset the Hardware ID of an account.
    """

    # Find profile
    exists = await app.state.users.find_one({"username": username})

    # Return error if it account does not exist
    if not exists:
        return {"status": encrypt.text("Unable to locate that account.")}

    # Reset hardware ID and increment reset counter by 1
    await app.state.users.update_one(
        {"username": username},
        {"$set": {"hardware_id": "", "resets": (exists["hwid_resets"] + 1)}},
    )

    return {"status": encrypt.success()}


@app.patch("/password", dependencies=[Depends(_check_admin)])
@limiter.limit("3/minute")
async def reset_password(request: Request, username: str, new_password: str) -> dict:
    """
    [Admin]: Change a user's password.
    """

    # Find profile
    exists = await app.state.users.find_one({"username": username})

    # Return error if account does not exist
    if not exists:
        return {"status": encrypt.text("Unable to locate that account.")}

    # Change password to new password
    await app.state.users.update_one(
        {"username": username},
        {"$set": {"password": new_password}},
    )

    return {"status": encrypt.success()}


@app.patch("/note", dependencies=[Depends(_check_admin)])
@limiter.limit("3/minute")
async def change_note(request: Request, username: str, note: str) -> dict:
    """
    [Admin]: Change a user's account note.
    """

    # Find profile
    exists = await app.state.users.find_one({"username": username})

    # Return error if account does not exist
    if not exists:
        return {"status": encrypt.text("Unable to locate that account.")}

    # Add note to account
    await app.state.users.update_one(
        {"username": username},
        {"$set": {"note": note}},
    )

    return {"status": encrypt.success()}


@app.get("/license", dependencies=[Depends(_check_admin)])
@limiter.limit("3/minute")
async def generate_license(request: Request) -> dict:
    """
    [Admin]: Generate a license key for user registration.
    """

    # Generate a license key
    license_key, creation_time = await create_license()

    return {"license": encrypt.text(license_key), "date_created": creation_time}


@app.get("/stats", dependencies=[Depends(_check_admin)])
@limiter.limit("5/minute")
async def app_statistics(request: Request) -> dict:
    """
    [Admin]: Display database user statistics.
    """

    # Lazy estimate the user & license totals
    total_users = await app.state.users.estimated_document_count()
    total_licenses = await app.state.licenses.estimated_document_count()

    return {
        "total_users": encrypt.text(str(total_users)),
        "total_licenses": encrypt.text(str(total_licenses)),
    }
