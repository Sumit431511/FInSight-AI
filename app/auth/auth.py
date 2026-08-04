import sqlite3
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from .security import (
    SECRET_KEY,
    ALGORITHM,
    verify_password,
    create_access_token,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)

from app.config import get_data_dir

DB_NAME = str(get_data_dir("roles_docs.db"))


def authenticate_user(username: str, password: str):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT password, role
        FROM users
        WHERE username = ?
        """,
        (username,),
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    hashed_password, role = row

    if not verify_password(password, hashed_password):
        return None

    return {
        "username": username,
        "role": role,
    }


def login_user(username: str, password: str):

    user = authenticate_user(
        username,
        password,
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    token = create_access_token(
        {
            "sub": user["username"],
            "role": user["role"],
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"],
    }


def get_current_user(
    token: str = Depends(oauth2_scheme),
):

    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        username = payload.get("sub")

        role = payload.get("role")

        if username is None:
            raise credentials_exception

        return {
            "username": username,
            "role": role,
        }

    except JWTError:
        raise credentials_exception