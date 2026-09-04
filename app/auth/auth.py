import sqlite3
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from .security import (
    SECRET_KEY,
    ALGORITHM,
    verify_password,
    create_access_token,
    hash_password,
    password_needs_rehash,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)

from app.db import get_sqlite_conn


def authenticate_user(username: str, password: str):
    with get_sqlite_conn() as conn:
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

    if row is None:
        return None

    hashed_password = row["password"]
    role = row["role"]

    if not verify_password(password, hashed_password):
        return None

    # Upgrade legacy SHA-256 hashes and Argon2 hashes using older parameters.
    if not hashed_password.startswith("$argon2") or password_needs_rehash(hashed_password):
        with get_sqlite_conn() as conn:
            conn.execute(
                "UPDATE users SET password = ? WHERE username = ?",
                (hash_password(password), username),
            )
            conn.commit()

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

        token_id = payload.get("jti")
        if not username:
            raise credentials_exception

        # Token role claims can become stale after an administrator changes a user.
        with get_sqlite_conn() as conn:
            if token_id:
                revoked = conn.execute(
                    "SELECT 1 FROM revoked_tokens WHERE jti = ?", (token_id,)
                ).fetchone()
                if revoked is not None:
                    raise credentials_exception
            row = conn.execute(
                "SELECT username, role FROM users WHERE username = ?", (username,)
            ).fetchone()
        if row is None:
            raise credentials_exception

        return {
            "username": row["username"],
            "role": row["role"],
        }

    except JWTError:
        raise credentials_exception
