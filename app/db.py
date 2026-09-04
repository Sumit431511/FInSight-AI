"""
Centralized database connection management.
Provides context-managed SQLite connections and a shared thread-safe DuckDB connection.
"""

import sqlite3
import duckdb
from contextlib import contextmanager
from app.config import get_data_dir

DB_PATH = get_data_dir("roles_docs.db")
DUCKDB_PATH = get_data_dir("static", "data", "structured_queries.duckdb")


@contextmanager
def get_sqlite_conn():
    """Context manager providing a SQLite connection with Row factory."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


_duck_conn = None


def get_duckdb():
    """Returns a shared DuckDB connection initialized with metadata tables."""
    global _duck_conn
    if _duck_conn is None:
        DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            _duck_conn = duckdb.connect(str(DUCKDB_PATH))
        except Exception as exc:
            print(f"DuckDB file connection failed, using in-memory fallback: {exc}")
            _duck_conn = duckdb.connect(":memory:")

        _duck_conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tables_metadata (
                table_name TEXT,
                role TEXT
            )
            """
        )
    return _duck_conn
