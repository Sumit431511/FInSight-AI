import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_project_root() -> Path:
    env_root = os.getenv("PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def get_data_dir(*parts: str) -> Path:
    return get_project_root().joinpath(*parts)


def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def get_jwt_secret() -> str:
    return get_env("JWT_SECRET_KEY") or get_env("SECRET_KEY") or "dev-secret-key-change-me"
