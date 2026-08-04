from app.auth.security import hash_password, verify_password


def test_verify_password_accepts_sha256_hash():
    hashed = hash_password("admin123")
    assert verify_password("admin123", hashed) is True


def test_hash_password_is_deterministic():
    hashed = hash_password("admin123")
    assert len(hashed) == 64
    assert verify_password("admin123", hashed) is True
