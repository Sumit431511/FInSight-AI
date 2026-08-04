import os
import time
import sqlite3
import duckdb
import pandas as pd

from pathlib import Path
from typing import List
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from pydantic import BaseModel
from app.config import get_project_root, get_data_dir
from app.rag_evaluator.dashboard import get_dashboard_data

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
)

from fastapi.responses import JSONResponse

# ==============================
# JWT Authentication
# ==============================

from app.auth.auth import (
    login_user,
    get_current_user,
)

from app.auth.schemas import LoginRequest

from app.auth.security import hash_password

# ==============================
# RAG
# ==============================

from .rag_utils.rag_module import (
    run_indexer,
    vectorstore,
    get_rag_chain,
)

from .rag_utils.query_classifier import (
    detect_query_type_llm,
)

from .rag_utils.csv_query import ask_csv

from .rag_utils.rag_chain import ask_rag

# ==============================
# Evaluation Framework
# ==============================

from app.rag_evaluator.logger import (
    log_chat,
)

from app.rag_evaluator.metrics import (
    build_metrics,
)


from app.rag_evaluator.online_evaluator import (
    evaluate_chat,
)

load_dotenv()

# ===========================================================
# FastAPI Lifespan
# ===========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    create_default_user()

    yield


app = FastAPI(
    lifespan=lifespan
)

# ===========================================================
# DuckDB
# ===========================================================

DUCKDB_DIR = get_data_dir("static", "data")

DUCKDB_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DUCKDB_PATH = DUCKDB_DIR / "structured_queries.duckdb"

try:
    duck_conn = duckdb.connect(
        str(DUCKDB_PATH)
    )
except Exception as exc:
    print(f"DuckDB file connection failed, using in-memory fallback: {exc}")
    duck_conn = duckdb.connect(":memory:")

duck_conn.execute(
    """
    CREATE TABLE IF NOT EXISTS tables_metadata (

        table_name TEXT,

        role TEXT

    )
    """
)

# ===========================================================
# SQLite
# ===========================================================

DB_PATH = get_data_dir("roles_docs.db")

conn = sqlite3.connect(
    DB_PATH,
    check_same_thread=False,
)

c = conn.cursor()

c.executescript(
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

CREATE TABLE IF NOT EXISTS documents(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    filename TEXT,

    role TEXT,

    filepath TEXT,

    headers_str TEXT,

    embedded INTEGER DEFAULT 0

);
"""
)

conn.commit()

# ===========================================================
# Default Admin
# ===========================================================

def create_default_user():

    conn_local = sqlite3.connect(
        DB_PATH
    )

    cursor = conn_local.cursor()

    cursor.execute(

        """
        INSERT OR IGNORE
        INTO roles(role_name)
        VALUES(?)
        """,

        ("C-Level",)

    )

    password = hash_password(
        "admin123"
    )

    try:

        cursor.execute(

            """
            INSERT INTO users(

                username,

                password,

                role

            )

            VALUES(?,?,?)

            """,

            (

                "admin",

                password,

                "C-Level",

            )

        )

        conn_local.commit()

        print(
            "Default Admin Created"
        )

    except sqlite3.IntegrityError:

        print(
            "Admin already exists."
        )

    conn_local.close()

# ===========================================================
# Models
# ===========================================================

class ChatRequest(BaseModel):

    question: str

# ===========================================================
# Health and Root
# ===========================================================

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


# ===========================================================
# Login
# ===========================================================

@app.post("/login")
def login(data: LoginRequest):

    return login_user(
        data.username,
        data.password,
    )


# ===========================================================
# Roles
# ===========================================================

@app.get("/roles")
def get_roles(
    user=Depends(get_current_user)
):

    c.execute(
        "SELECT role_name FROM roles"
    )

    roles = [
        row[0]
        for row in c.fetchall()
    ]

    return {
        "roles": roles
    }


# ===========================================================
# Documents
# ===========================================================

@app.get("/documents")
def get_documents(
    user=Depends(get_current_user)
):

    if user["role"] != "C-Level":

        raise HTTPException(

            status_code=403,

            detail="Only C-Level can view documents."

        )

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT

            id,

            filename,

            role,

            embedded

        FROM documents

        ORDER BY role,
                 filename

        """

    )

    rows = cursor.fetchall()

    conn.close()

    return {

        "documents":

        [

            dict(row)

            for row in rows

        ]

    }


@app.get("/dashboard")
def dashboard(
    user=Depends(get_current_user)
):

    if user["role"] != "C-Level":

        raise HTTPException(
            status_code=403,
            detail="Only C-Level can access dashboard."
        )

    return get_dashboard_data()
# ===========================================================
# Create User
# ===========================================================

@app.post("/create-user")
def create_user(

    username: str = Form(...),

    password: str = Form(...),

    role: str = Form(...),

    user=Depends(get_current_user),

):

    if user["role"] != "C-Level":

        raise HTTPException(

            status_code=403,

            detail="Only C-Level can create users.",

        )

    c.execute(

        """
        SELECT 1

        FROM roles

        WHERE role_name = ?

        """,

        (role,)

    )

    if not c.fetchone():

        raise HTTPException(

            status_code=400,

            detail="Invalid role",

        )

    hashed_password = hash_password(
        password
    )

    try:

        c.execute(

            """
            INSERT INTO users(

                username,

                password,

                role

            )

            VALUES(?,?,?)

            """,

            (

                username,

                hashed_password,

                role,

            )

        )

        conn.commit()

        return {

            "message":

            f"User '{username}' created successfully."

        }

    except sqlite3.IntegrityError:

        raise HTTPException(

            status_code=400,

            detail="User already exists.",

        )


# ===========================================================
# Create Role
# ===========================================================

@app.post("/create-role")
def create_role(

    role_name: str = Form(...),

    user=Depends(get_current_user),

):

    if user["role"] != "C-Level":

        raise HTTPException(

            status_code=403,

            detail="Only C-Level can create roles.",

        )

    conn = sqlite3.connect(
        DB_PATH
    )

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT 1

        FROM roles

        WHERE role_name = ?

        """,

        (role_name,)

    )

    if cursor.fetchone():

        conn.close()

        raise HTTPException(

            status_code=400,

            detail=f"Role '{role_name}' already exists.",

        )

    cursor.execute(

        """
        INSERT INTO roles(role_name)

        VALUES(?)
        """,

        (role_name,)

    )

    conn.commit()

    conn.close()

    return {

        "message":

        f"Role '{role_name}' created successfully."

    }


# ===========================================================
# Upload Directory
# ===========================================================

UPLOAD_DIR = str(get_data_dir("static", "uploads"))

# ===========================================================
# Upload Documents (Multi Upload)
# ===========================================================

@app.post("/upload-docs")
async def upload_docs(

    files: List[UploadFile] = File(...),

    role: str = Form(...),

    user=Depends(get_current_user),

):

    uploaded = []

    failed = []

    role_dir = os.path.join(
        UPLOAD_DIR,
        role,
    )

    os.makedirs(
        role_dir,
        exist_ok=True,
    )

    for file in files:

        try:

            filename = file.filename

            extension = (
                Path(filename)
                .suffix
                .lower()
            )

            filepath = os.path.join(

                role_dir,

                filename,

            )

            data = await file.read()

            with open(
                filepath,
                "wb",
            ) as f:

                f.write(data)

            headers_str = None

            # =====================================
            # CSV Upload
            # =====================================

            if extension == ".csv":

                from io import BytesIO

                df = pd.read_csv(
                    BytesIO(data)
                )

                df1 = pd.read_csv(
                    filepath
                )

                table_name = (
                    Path(filepath)
                    .stem
                    .replace("-", "_")
                )

                headers = (
                    df1.columns.tolist()
                )

                headers_str = ",".join(
                    headers
                )

                duck_conn.execute(

                    f"""
                    CREATE OR REPLACE TABLE
                    {table_name}

                    AS

                    SELECT *

                    FROM df1
                    """

                )

                duck_conn.execute(

                    """
                    INSERT INTO
                    tables_metadata(

                        table_name,

                        role

                    )

                    VALUES(?,?)

                    """,

                    (

                        table_name,

                        role,

                    ),

                )

            # =====================================
            # Markdown Upload
            # =====================================

            elif extension == ".md":

                headers_str = None

            # =====================================
            # Invalid File
            # =====================================

            else:

                failed.append(
                    filename
                )

                continue

            conn = sqlite3.connect(
                DB_PATH
            )

            cursor = conn.cursor()

            cursor.execute(

                """
                INSERT INTO documents(

                    filename,

                    role,

                    filepath,

                    headers_str,

                    embedded

                )

                VALUES(?,?,?,?,?)

                """,

                (

                    filename,

                    role,

                    filepath,

                    headers_str,

                    0,

                ),

            )

            conn.commit()

            conn.close()

            uploaded.append(
                filename
            )

        except Exception as e:

            print(e)

            failed.append(
                file.filename
            )

    # =====================================
    # Rebuild Vector DB
    # =====================================

    run_indexer()

    return {

        "message":

        f"{len(uploaded)} file(s) uploaded successfully.",

        "uploaded":

        uploaded,

        "failed":

        failed,

    }
# ===========================================================
# Chat Endpoint
# ===========================================================

@app.post("/chat")
async def chat(
    req: ChatRequest,
    user=Depends(get_current_user),
):

    role = user["role"]
    username = user["username"]
    question = req.question

    # -----------------------------------
    # Start Timer
    # -----------------------------------

    start_time = time.perf_counter()

    mode = detect_query_type_llm(question)

    print(f"Detected Mode : {mode}")

    result = {}

    fallback_used = False

    # -----------------------------------
    # SQL
    # -----------------------------------

    if mode == "SQL":

        try:

            result = await ask_csv(
                question,
                role,
                username,
                return_sql=True,
            )

            if (
                result.get("error")
                or
                not result.get("answer", "").strip()
            ):

                raise ValueError(
                    "SQL Failed"
                )

        except Exception as e:

            print(e)

            result = await ask_rag(
                question,
                role,
            )

            fallback_used = True

            mode = "SQL → RAG"

    # -----------------------------------
    # Pure RAG
    # -----------------------------------

    elif mode == "RAG":

        result = await ask_rag(
            question,
            role,
        )

    # -----------------------------------
    # Hybrid
    # -----------------------------------

    else:

        sql_result = await ask_csv(

            question,

            role,

            username,

            return_sql=True,

        )

        rag_result = await ask_rag(

            question,

            role,

        )

        result = {

            "answer":

            "## 📊 Structured Data\n\n"

            + sql_result["answer"]

            + "\n\n---\n\n"

            + "## 📄 Retrieved Documents\n\n"

            + rag_result["answer"],

            "context":

            rag_result.get(
                "context",
                [],
            ),

        }

        if "sql" in sql_result:

            result["sql"] = sql_result["sql"]

    # -----------------------------------
    # Stop Timer
    # -----------------------------------

    latency = round(

        (
            time.perf_counter()
            -
            start_time
        )
        *1000,

        2,

    )

    # -----------------------------------
    # Extract Sources
    # -----------------------------------

    retrieved_docs = []

    sources = []

    for doc in result.get(
        "context",
        [],
    ):

        try:

            if isinstance(doc, dict):

                source = doc.get(
                    "metadata",
                    {}
                ).get(
                    "source",
                    "Unknown"
                )

            else:

                source = getattr(
                    doc,
                    "metadata",
                    {}
                ).get(
                    "source",
                    "Unknown"
                )

            retrieved_docs.append(
                source
            )

            sources.append(
                source
            )

        except Exception:

            pass

    # -----------------------------------
# Real AI Evaluation
# -----------------------------------

    contexts = []

    for doc in result.get("context", []):

        if isinstance(doc, dict):

            contexts.append(
                 doc.get(
                    "page_content",
                    ""
                )
            )

        else:

            contexts.append(
                 getattr(
                    doc,
                    "page_content",
                    ""
                )
            )

    retrieved_context = "\n\n".join(contexts)
    try:

        evaluation = evaluate_chat(

        question=question,

        answer=result.get(
          "answer",
         "",
         ),

        retrieved_context=retrieved_context,

        )

    except Exception as e:

        print(e)

        evaluation = {

            "faithfulness":0,

            "relevancy":0,

            "context_recall":0,

        }

    # -----------------------------------
    # Build Metrics
    # -----------------------------------

    metrics = build_metrics(

        evaluation,

        latency,

        retrieved_docs,

    )

    # -----------------------------------
    # Store Chat Log
    # -----------------------------------

    log_chat(

    username=username,

    role=role,

    question=question,

    mode=mode,

    answer=result.get("answer",""),

    latency=latency,

    fallback=fallback_used,

    sql_query=result.get("sql"),

    retrieved_docs=retrieved_docs,

    sources=sources,

    evaluation=metrics,

    )

    # -----------------------------------
    # Response
    # -----------------------------------

    return {

        "user":username,

        "role":role,

        "mode":mode,

        "fallback":fallback_used,

        "latency":latency,

        "confidence":metrics[
            "confidence"
        ],

        "answer":

        result.get(
            "answer",
            "",
        ),

        "context":

        result.get(
            "context",
            [],
        ),

        **(

            {

                "sql":

                result["sql"]

            }

            if "sql" in result

            else {}

        ),

    }
