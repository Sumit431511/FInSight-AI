"""
Authentication and User Management Routes.
"""

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException
from jose import JWTError, jwt
from app.auth.auth import login_user, get_current_user, oauth2_scheme
from app.auth.schemas import LoginRequest
from app.auth.security import ALGORITHM, SECRET_KEY, hash_password
from app.db import get_sqlite_conn
import sqlite3

router = APIRouter()


def _validate_role_name(role_name: str) -> str:
    value = role_name.strip()
    if len(value) < 2 or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9 -]{0,62}[A-Za-z0-9])?", value):
        raise HTTPException(
            status_code=422,
            detail="Role names must be 2-64 characters and contain only letters, numbers, spaces, or hyphens.",
        )
    return value


def _require_c_level(user: dict) -> None:
    if user["role"] != "C-Level":
        raise HTTPException(status_code=403, detail="Only C-Level can manage users.")


def _ensure_role_exists(role: str) -> str:
    role = _validate_role_name(role)
    with get_sqlite_conn() as conn:
        exists = conn.execute("SELECT 1 FROM roles WHERE role_name = ?", (role,)).fetchone()
    if exists is None:
        raise HTTPException(status_code=400, detail="Invalid role.")
    return role


@router.post("/login")
def login(data: LoginRequest):
    return login_user(data.username, data.password)


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), user=Depends(get_current_user)):
    """Revoke the current JWT so browser state cannot restore a logged-out session."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_id = payload.get("jti")
        expires_at = int(payload.get("exp", 0))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    if token_id:
        now = int(datetime.now(timezone.utc).timestamp())
        with get_sqlite_conn() as conn:
            conn.execute("DELETE FROM revoked_tokens WHERE expires_at < ?", (now,))
            conn.execute(
                "INSERT OR REPLACE INTO revoked_tokens(jti, expires_at) VALUES(?, ?)",
                (token_id, expires_at),
            )
            conn.commit()
    return {"message": "Logged out successfully."}


@router.get("/roles")
def get_roles(user=Depends(get_current_user)):
    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role_name FROM roles")
        roles = [row["role_name"] for row in cursor.fetchall()]
    return {"roles": roles}


@router.get("/users/me")
def get_my_profile(user=Depends(get_current_user)):
    return user


@router.get("/users")
def list_users(user=Depends(get_current_user)):
    _require_c_level(user)
    with get_sqlite_conn() as conn:
        rows = conn.execute(
            "SELECT id, username, role FROM users ORDER BY username COLLATE NOCASE"
        ).fetchall()
    return {"users": [dict(row) for row in rows]}


@router.post("/create-user")
def create_user(
    username: str = Form(..., min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$"),
    password: str = Form(..., min_length=8, max_length=256),
    role: str = Form(..., min_length=2, max_length=64),
    user=Depends(get_current_user),
):
    _require_c_level(user)

    role = _ensure_role_exists(role)
    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        try:
            cursor.execute(
                """
                INSERT INTO users(username, password, role)
                VALUES(?,?,?)
                """,
                (username, hashed_password, role),
            )
            conn.commit()
            return {"message": f"User '{username}' created successfully."}
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=400,
                detail="User already exists.",
            )


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str = Form(..., min_length=2, max_length=64),
    user=Depends(get_current_user),
):
    _require_c_level(user)
    role = _ensure_role_exists(role)
    with get_sqlite_conn() as conn:
        target = conn.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if target is None:
            raise HTTPException(status_code=404, detail="User not found.")
        if target["role"] == "C-Level" and role != "C-Level":
            c_level_count = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'C-Level'"
            ).fetchone()[0]
            if c_level_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot remove the last C-Level administrator.")
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        conn.commit()
    return {"message": f"Role updated for '{target['username']}'."}


@router.put("/users/{user_id}/password")
def reset_user_password(
    user_id: int,
    password: str = Form(..., min_length=8, max_length=256),
    user=Depends(get_current_user),
):
    _require_c_level(user)
    with get_sqlite_conn() as conn:
        target = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if target is None:
            raise HTTPException(status_code=404, detail="User not found.")
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (hash_password(password), user_id))
        conn.commit()
    return {"message": f"Password reset for '{target['username']}'."}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, user=Depends(get_current_user)):
    _require_c_level(user)
    with get_sqlite_conn() as conn:
        target = conn.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if target is None:
            raise HTTPException(status_code=404, detail="User not found.")
        if target["username"] == user["username"]:
            raise HTTPException(status_code=400, detail="You cannot delete your own account.")
        if target["role"] == "C-Level":
            c_level_count = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'C-Level'"
            ).fetchone()[0]
            if c_level_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot delete the last C-Level administrator.")
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    return {"message": f"User '{target['username']}' deleted."}


@router.post("/create-role")
def create_role(
    role_name: str = Form(..., min_length=2, max_length=64),
    user=Depends(get_current_user),
):
    _require_c_level(user)

    role_name = _validate_role_name(role_name)
    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM roles WHERE role_name = ?",
            (role_name,),
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"Role '{role_name}' already exists.",
            )

        cursor.execute(
            "INSERT INTO roles(role_name) VALUES(?)",
            (role_name,),
        )
        conn.commit()

    return {"message": f"Role '{role_name}' created successfully."}
