from datetime import datetime, timedelta, timezone
from jose import jwt
from dotenv import load_dotenv
from passlib.context import CryptContext
from passlib.hash import argon2

from app.config import get_jwt_secret

load_dotenv()

SECRET_KEY = get_jwt_secret()

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

password_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False

    try:
        return password_context.verify(password, hashed_password)
    except Exception:
        try:
            return argon2.verify(password, hashed_password)
        except Exception:
            return False

def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update(
        {
            "exp": expire
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return encoded_jwt