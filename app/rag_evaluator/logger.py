import sqlite3
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "chat_logs.db"

DB_PATH.parent.mkdir(exist_ok=True)


def init_logger():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_logs(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        timestamp TEXT,

        username TEXT,

        role TEXT,

        question TEXT,

        mode TEXT,

        fallback INTEGER,

        latency_ms REAL,

        answer TEXT,

        sql_query TEXT,

        retrieved_docs TEXT,

        sources TEXT,

        faithfulness REAL,

        relevancy REAL,

        context_recall REAL,

        confidence REAL,

        hallucination REAL,

        retriever_hit_rate REAL,

        source_count INTEGER

    )
    """)

    conn.commit()

    conn.close()


init_logger()


def log_chat(

    username,

    role,

    question,

    mode,

    answer,

    latency,

    fallback=False,

    sql_query=None,

    retrieved_docs=None,

    sources=None,

    evaluation=None,

    ):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
    """
    INSERT INTO chat_logs(

        timestamp,

        username,

        role,

        question,

        mode,

        fallback,

        latency_ms,

        answer,

        sql_query,

        retrieved_docs,

        sources,

        faithfulness,

        relevancy,

        context_recall,

        confidence,

        hallucination,

        retriever_hit_rate,

        source_count

    )

    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

    """,

    (

        datetime.now().isoformat(),

        username,

        role,

        question,

        mode,

        int(fallback),

        latency,

        answer,

        sql_query,

        json.dumps(retrieved_docs or []),

        json.dumps(sources or []),

        evaluation.get("faithfulness"),

        evaluation.get("relevancy"),

        evaluation.get("context_recall"),

        evaluation.get("confidence"),

        evaluation.get("hallucination"),

        evaluation.get("retriever_hit_rate"),

        evaluation.get("source_count"),

    )

)

    conn.commit()

    conn.close()