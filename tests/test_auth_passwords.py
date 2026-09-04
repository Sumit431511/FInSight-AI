import hashlib
from app.auth.security import hash_password, verify_password


def test_verify_password_accepts_argon2_hash():
    hashed = hash_password("admin123")
    assert hashed.startswith("$argon2")
    assert verify_password("admin123", hashed) is True
    assert verify_password("wrongpass", hashed) is False


def test_verify_password_supports_legacy_sha256_fallback():
    legacy_sha256 = hashlib.sha256("admin123".encode("utf-8")).hexdigest()
    assert verify_password("admin123", legacy_sha256) is True
    assert verify_password("wrongpass", legacy_sha256) is False

