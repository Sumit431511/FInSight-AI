"""
Document Management and Upload Routes.
"""

import os
import re
import uuid
from io import BytesIO
from pathlib import Path
from typing import List

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from app.auth.auth import get_current_user
from app.config import get_data_dir
from app.db import get_duckdb, get_sqlite_conn
from app.rag_utils.rag_module import delete_document_vectors, run_indexer

router = APIRouter()

UPLOAD_DIR = get_data_dir("static", "uploads")
ALLOWED_EXTENSIONS = {".csv", ".md", ".txt", ".pdf", ".docx"}
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))


def _safe_display_filename(filename: str | None) -> str:
    """Keep a human-readable filename without allowing it to control a path."""
    candidate = Path(filename or "upload").name
    candidate = re.sub(r"[^A-Za-z0-9._ -]", "_", candidate).strip(" .")
    return candidate[:180] or "upload"


@router.get("/documents")
def get_documents(user=Depends(get_current_user)):
    if user["role"] != "C-Level":
        raise HTTPException(
            status_code=403,
            detail="Only C-Level can view documents.",
        )

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, filename, role, embedded, status, error_message, created_at
            FROM documents
            ORDER BY role, filename
            """
        )
        rows = cursor.fetchall()

    return {"documents": [dict(row) for row in rows]}


@router.post("/upload-docs")
async def upload_docs(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    role: str = Form(...),
    user=Depends(get_current_user),
):
    if user["role"] != "C-Level":
        raise HTTPException(status_code=403, detail="Only C-Level can upload documents.")

    with get_sqlite_conn() as conn:
        role_exists = conn.execute(
            "SELECT 1 FROM roles WHERE role_name = ?", (role,)
        ).fetchone()
    if role_exists is None:
        raise HTTPException(status_code=400, detail="Invalid document role.")

    if not files or len(files) > 10:
        raise HTTPException(status_code=400, detail="Upload between 1 and 10 files at a time.")

    uploaded = []
    failed = []
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    duck_conn = get_duckdb()

    for file in files:
        filepath = None
        table_name = None
        try:
            filename = _safe_display_filename(file.filename)
            extension = Path(filename).suffix.lower()

            if extension not in ALLOWED_EXTENSIONS:
                failed.append(filename)
                continue

            data = await file.read()
            if not data or len(data) > MAX_UPLOAD_BYTES:
                failed.append(filename)
                continue

            document_key = uuid.uuid4().hex
            filepath = UPLOAD_DIR / f"{document_key}_{filename}"

            with open(filepath, "wb") as f:
                f.write(data)

            headers_str = None
            if extension == ".csv":
                df1 = pd.read_csv(BytesIO(data))
                if df1.empty and not list(df1.columns):
                    raise ValueError("CSV file has no columns.")
                table_name = f"doc_{document_key}"
                headers = df1.columns.tolist()
                headers_str = ",".join(headers)

                duck_conn.execute(
                    f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df1"
                )

                duck_conn.execute(
                    """
                    INSERT INTO tables_metadata(table_name, role)
                    VALUES(?,?)
                    """,
                    (table_name, role.lower()),
                )

            with get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO documents(
                        filename, role, filepath, headers_str, table_name, embedded, status, created_at
                    )
                    VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                    """,
                    (filename, role, str(filepath), headers_str, table_name, 0, "pending"),
                )
                conn.commit()

            uploaded.append(filename)

        except Exception as e:
            print(f"Error uploading document {file.filename}: {e}")
            if table_name:
                try:
                    duck_conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                    duck_conn.execute("DELETE FROM tables_metadata WHERE table_name = ?", (table_name,))
                except Exception:
                    pass
            if filepath and filepath.exists():
                filepath.unlink()
            failed.append(file.filename)

    if uploaded:
        background_tasks.add_task(run_indexer)

    return {
        "message": f"{len(uploaded)} file(s) uploaded successfully.",
        "uploaded": uploaded,
        "failed": failed,
        "indexing_started": bool(uploaded),
    }


@router.post("/documents/{document_id}/retry")
def retry_document_indexing(
    document_id: int,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    if user["role"] != "C-Level":
        raise HTTPException(status_code=403, detail="Only C-Level can retry document indexing.")

    with get_sqlite_conn() as conn:
        document = conn.execute("SELECT id FROM documents WHERE id = ?", (document_id,)).fetchone()
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        conn.execute(
            "UPDATE documents SET embedded = 0, status = 'pending', error_message = NULL WHERE id = ?",
            (document_id,),
        )
        conn.commit()
    background_tasks.add_task(run_indexer)
    return {"message": "Document indexing retry started.", "document_id": document_id}


@router.delete("/documents/{document_id}")
def delete_document(document_id: int, user=Depends(get_current_user)):
    if user["role"] != "C-Level":
        raise HTTPException(status_code=403, detail="Only C-Level can delete documents.")

    with get_sqlite_conn() as conn:
        document = conn.execute(
            "SELECT id, filepath, table_name FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found.")

    try:
        delete_document_vectors(document_id)
        table_name = document["table_name"]
        if table_name and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
            duck_conn = get_duckdb()
            duck_conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            duck_conn.execute("DELETE FROM tables_metadata WHERE table_name = ?", (table_name,))

        stored_path = Path(document["filepath"]).resolve()
        upload_root = UPLOAD_DIR.resolve()
        if stored_path.is_relative_to(upload_root) and stored_path.exists():
            stored_path.unlink()

        with get_sqlite_conn() as conn:
            conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            conn.commit()
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to delete the document safely.")

    return {"message": "Document deleted successfully.", "document_id": document_id}
