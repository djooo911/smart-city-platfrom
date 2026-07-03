"""
Unit tests for app/security/password.py. Pure logic, no infra.
"""

import pytest

from app.security.password import hash_password, verify_password

pytestmark = pytest.mark.unit


def test_verify_password_accepts_correct_password():
    password_hash = hash_password("correct-horse-battery-staple")

    assert verify_password("correct-horse-battery-staple", password_hash) is True


def test_verify_password_rejects_wrong_password():
    password_hash = hash_password("correct-horse-battery-staple")

    assert verify_password("wrong-password", password_hash) is False


def test_hash_password_uses_a_random_salt():
    hash_a = hash_password("same-password")
    hash_b = hash_password("same-password")

    assert hash_a != hash_b


def test_verify_password_rejects_malformed_hash():
    assert verify_password("anything", "not-a-valid-hash-format") is False


def test_hash_password_stores_iteration_count_and_salt_in_plain_text():
    password_hash = hash_password("secret")

    iterations, salt, digest = password_hash.split("$")
    assert iterations.isdigit()
    assert len(salt) == 32  # 16 bytes hex-encoded
    assert len(digest) == 64  # sha256 hex-encoded
