from passlib.hash import argon2

from app.auth.security import verify_password


def test_verify_password_accepts_argon2_hash():
    hashed = argon2.hash("admin123")
    assert verify_password("admin123", hashed) is True
