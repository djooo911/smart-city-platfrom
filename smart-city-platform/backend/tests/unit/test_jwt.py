"""
Unit tests for app/security/jwt.py. Pure logic, no infra -- secret_key is
passed explicitly (see jwt.py's docstring), so these tests need no .env.
"""

import jwt as pyjwt
import pytest

from app.domain.entities.enums import Role
from app.security.jwt import create_access_token, decode_access_token

pytestmark = pytest.mark.unit

SECRET_KEY = "test-secret-key"


def test_decode_returns_embedded_claims():
    token = create_access_token("alice", Role.OPERATOR, SECRET_KEY, expires_minutes=60)

    payload = decode_access_token(token, SECRET_KEY)

    assert payload["sub"] == "alice"
    assert payload["role"] == "operator"


def test_decode_rejects_token_signed_with_a_different_key():
    token = create_access_token("alice", Role.OPERATOR, SECRET_KEY, expires_minutes=60)

    with pytest.raises(pyjwt.InvalidTokenError):
        decode_access_token(token, "a-different-secret-key")


def test_decode_rejects_expired_token():
    token = create_access_token("alice", Role.VIEWER, SECRET_KEY, expires_minutes=-1)

    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_access_token(token, SECRET_KEY)
