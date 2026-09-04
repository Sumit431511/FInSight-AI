"""
FinSight Enterprise AI Assistant - FastAPI Main Server Entrypoint.
"""

import os
import re
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_data_dir
from app.db import get_sqlite_conn, get_duckdb
from app.auth.security import hash_password

from app.routers import (
    auth_routes,
    document_routes,
    chat_routes,
    dashboard_routes,
)

load_dotenv()

DB_PATH = get_data_dir("roles_docs.db")


def init_db_schema():
    """Initialize SQLite tables if they do not exist."""
    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            );

            CREATE TABLE IF NOT EXISTS roles(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS revoked_tokens(
                jti TEXT PRIMARY KEY,
                expires_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS documents(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                role TEXT,
                filepath TEXT,
                headers_str TEXT,
                table_name TEXT UNIQUE,
                embedded INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                error_message TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        existing_columns = {
            row["name"] for row in cursor.execute("PRAGMA table_info(documents)").fetchall()
        }
        if "table_name" not in existing_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN table_name TEXT")
        if "status" not in existing_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN status TEXT")
        if "error_message" not in existing_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN error_message TEXT")
        if "created_at" not in existing_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN created_at TEXT")
        # Preserve safely named legacy CSV tables created before table_name existed.
        for row in cursor.execute(
            "SELECT id, filename FROM documents WHERE table_name IS NULL AND headers_str IS NOT NULL"
        ).fetchall():
            legacy_name = Path(row["filename"]).stem.replace("-", "_")
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", legacy_name):
                cursor.execute(
                    "UPDATE documents SET table_name = ? WHERE id = ?",
                    (legacy_name, row["id"]),
                )
        cursor.execute(
            """
            UPDATE documents
            SET status = CASE WHEN embedded = 1 THEN 'indexed' ELSE 'pending' END
            WHERE status IS NULL OR status = ''
            """
        )
        conn.commit()


def create_default_user():
    """Seed initial C-Level role and default admin user."""
    default_pw = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO roles(role_name) VALUES(?)",
            ("C-Level",),
        )

        password = hash_password(default_pw)
        try:
            cursor.execute(
                """
                INSERT INTO users(username, password, role)
                VALUES(?,?,?)
                """,
                ("admin", password, "C-Level"),
            )
            conn.commit()
            print("Default Admin User Initialized.")
        except sqlite3.IntegrityError:
            print("Admin user already exists.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_schema()
    get_duckdb()
    create_default_user()
    yield


app = FastAPI(
    title="FinSight AI Assistant API",
    description="Enterprise Hybrid RAG + SQL Assistant with RBAC & AI Evaluation",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS Middleware Setup
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
allowed_origins = [frontend_url]
if os.getenv("ENVIRONMENT", "development").lower() not in {"production", "prod"}:
    allowed_origins.extend(["http://localhost:8501", "http://127.0.0.1:8501"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(allowed_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_routes.router, tags=["Authentication"])
app.include_router(document_routes.router, tags=["Documents"])
app.include_router(chat_routes.router, tags=["Chat"])
app.include_router(dashboard_routes.router, tags=["Dashboard"])


@app.get("/")
def root():
    return {
        "message": "FinSight RBAC RAG API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
