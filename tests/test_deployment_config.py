from pathlib import Path

from app.config import get_project_root, get_data_dir, get_env


def test_project_root_points_to_workspace():
    root = get_project_root()
    assert root.exists()
    assert (root / "requirements.txt").exists()
    assert (root / "app").exists()


def test_data_dir_is_inside_project():
    data_dir = get_data_dir("static", "data")
    assert data_dir.is_absolute()
    assert str(data_dir).startswith(str(get_project_root()))


def test_env_uses_fallback_when_missing():
    assert get_env("DEPLOYMENT_TEST_VALUE", "fallback") == "fallback"
