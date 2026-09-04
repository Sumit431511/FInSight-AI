import pytest
from fastapi.testclient import TestClient

from app.auth.auth import get_current_user
from app.config import get_jwt_secret
from app.main import app
from app.rag_utils.csv_query import extract_tables_from_sql, is_safe_query
from app.routers.auth_routes import _validate_role_name
from app.routers.document_routes import _safe_display_filename


def test_upload_filename_cannot_control_storage_path():
    filename = _safe_display_filename("../../Finance/quarterly.csv")
    assert filename == "quarterly.csv"
    assert "/" not in filename
    assert "\\" not in filename


def test_role_name_rejects_path_and_sql_characters():
    assert _validate_role_name("C-Level") == "C-Level"
    with pytest.raises(Exception):
        _validate_role_name("../Finance")
    with pytest.raises(Exception):
        _validate_role_name("Finance; DROP TABLE users")


def test_production_requires_a_jwt_secret(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        get_jwt_secret()


def test_non_c_level_cannot_upload_documents():
    app.dependency_overrides[get_current_user] = lambda: {"username": "hr", "role": "HR"}
    try:
        with TestClient(app) as client:
            response = client.post(
                "/upload-docs",
                data={"role": "HR"},
                files={"files": ("policy.md", b"internal policy", "text/markdown")},
            )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_sql_guard_allows_one_select_and_rejects_unsafe_sql():
    query = "SELECT * FROM doc_alpha JOIN doc_beta ON doc_alpha.id = doc_beta.id"
    assert is_safe_query(query) is True
    assert set(extract_tables_from_sql(query)) == {"doc_alpha", "doc_beta"}
    assert is_safe_query("SELECT 1; DELETE FROM users") is False
    assert is_safe_query("DROP TABLE users") is False
