from passlib.hash import argon2

from app.auth.security import hash_password, verify_password


def test_verify_password_accepts_argon2_hash():
    hashed = argon2.hash("admin123")
    assert verify_password("admin123", hashed) is True


def test_hash_password_uses_argon2_without_crashing():
    hashed = hash_password("admin123")
    assert hashed.startswith("$argon2")
    assert verify_password("admin123", hashed) is True
