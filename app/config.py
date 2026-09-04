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
    """Return the persistent-data root, configurable independently from source code."""
    storage_root = os.getenv("DATA_DIR")
    root = Path(storage_root).expanduser().resolve() if storage_root else get_project_root()
    return root.joinpath(*parts)


def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def get_jwt_secret() -> str:
    secret = get_env("JWT_SECRET_KEY") or get_env("SECRET_KEY")
    environment = (get_env("ENVIRONMENT", "development") or "development").lower()
    if secret:
        return secret
    if environment in {"production", "prod"}:
        raise RuntimeError("JWT_SECRET_KEY must be configured in production.")
    return "dev-secret-key-change-me"


def get_groq_model() -> str:
    """Return the Groq model used across chat, SQL, RAG, and evaluation flows."""
    return get_env("GROQ_MODEL", "openai/gpt-oss-120b") or "openai/gpt-oss-120b"
