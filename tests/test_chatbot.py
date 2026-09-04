import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.auth.security import create_access_token
from app.main import app

client = TestClient(app)


@pytest.fixture
def c_level_auth_headers():
    token = create_access_token({"sub": "admin", "role": "C-Level"})
    return {"Authorization": f"Bearer {token}"}


def test_create_role_c_level(c_level_auth_headers):
    role_name = "Test Engineering"
    res = client.post(
        "/create-role", headers=c_level_auth_headers, data={"role_name": role_name}
    )
    assert res.status_code in (200, 400)
    if res.status_code == 200:
        assert f"Role '{role_name}' created" in res.json().get("message", "")


def test_create_user_c_level(c_level_auth_headers):
    client.post(
        "/create-role", headers=c_level_auth_headers, data={"role_name": "Marketing"}
    )

    res = client.post(
        "/create-user",
        headers=c_level_auth_headers,
        data={"username": "test_newuser", "password": "newpass123", "role": "Marketing"},
    )
    assert res.status_code in (200, 400)


@patch("app.routers.document_routes.run_indexer", return_value={"indexed": [], "failed": []})
def test_upload_csv_doc(mock_indexer, c_level_auth_headers):
    content = b"Name,Policy\nAdmin,Compliant"
    file = io.BytesIO(content)
    client.post(
        "/create-role", headers=c_level_auth_headers, data={"role_name": "csvrole"}
    )

    res = client.post(
        "/upload-docs",
        headers=c_level_auth_headers,
        files={"files": ("test.csv", file, "text/csv")},
        data={"role": "csvrole"},
    )

    assert res.status_code == 200
    assert "uploaded successfully" in res.json()["message"]


@patch("app.routers.document_routes.run_indexer", return_value={"indexed": [], "failed": []})
def test_upload_md_doc(mock_indexer, c_level_auth_headers):
    content = b"# Engineering Policies\nFollow coding guidelines."
    file = io.BytesIO(content)
    client.post(
        "/create-role", headers=c_level_auth_headers, data={"role_name": "mdrole"}
    )

    res = client.post(
        "/upload-docs",
        headers=c_level_auth_headers,
        files={"files": ("guide.md", file, "text/markdown")},
        data={"role": "mdrole"},
    )

    assert res.status_code == 200
    assert "uploaded successfully" in res.json()["message"]


@patch("app.routers.chat_routes._async_evaluate_and_log")
@patch("app.routers.chat_routes.detect_query_type_llm", return_value="RAG")
@patch("app.routers.chat_routes.ask_rag", return_value={"answer": "This is RAG response"})
def test_chat_rag_mode(mock_ask_rag, mock_detect, mock_evaluate, c_level_auth_headers):
    res = client.post(
        "/chat",
        headers=c_level_auth_headers,
        json={"question": "What are engineering policies?"},
    )
    assert res.status_code == 200
    assert res.json()["mode"] == "RAG"
    assert res.json()["answer"] == "This is RAG response"


@patch("app.routers.chat_routes._async_evaluate_and_log")
@patch("app.routers.chat_routes.detect_query_type_llm", return_value="SQL")
@patch(
    "app.routers.chat_routes.ask_csv",
    return_value={"answer": "Here is the SQL data", "sql": "SELECT * FROM table"},
)
def test_chat_sql_mode(mock_ask_csv, mock_detect, mock_evaluate, c_level_auth_headers):
    res = client.post(
        "/chat",
        headers=c_level_auth_headers,
        json={"question": "List all employees in HR"},
    )
    assert res.status_code == 200
    assert res.json()["mode"] == "SQL"
    assert res.json()["answer"] == "Here is the SQL data"
    assert "sql" in res.json()


def test_create_role_no_auth():
    res = client.post("/create-role", data={"role_name": "bad"})
    assert res.status_code in (401, 403)


def test_c_level_can_list_users_and_cannot_delete_self(c_level_auth_headers):
    users_response = client.get("/users", headers=c_level_auth_headers)
    assert users_response.status_code == 200
    users = users_response.json()["users"]
    admin = next(user for user in users if user["username"] == "admin")

    delete_response = client.delete(f"/users/{admin['id']}", headers=c_level_auth_headers)
    assert delete_response.status_code == 400


def test_logout_revokes_the_current_token(c_level_auth_headers):
    logout_response = client.post("/logout", headers=c_level_auth_headers)
    assert logout_response.status_code == 200

    restored_session = client.get("/roles", headers=c_level_auth_headers)
    assert restored_session.status_code == 401
