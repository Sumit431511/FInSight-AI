import hashlib
import os
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from jose import jwt
from dotenv import load_dotenv

from app.config import get_jwt_secret

load_dotenv()

SECRET_KEY = get_jwt_secret()

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

ph = PasswordHasher()


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False

    if not hashed_password.startswith("$argon2"):
        return hashlib.sha256(password.encode("utf-8")).hexdigest() == hashed_password

    try:
        return ph.verify(hashed_password, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(hashed_password: str) -> bool:
    """Return whether an Argon2 password should be upgraded after login."""
    return hashed_password.startswith("$argon2") and ph.check_needs_rehash(hashed_password)

def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update(
        {
            "exp": expire,
            "jti": uuid4().hex,
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return encoded_jwt
