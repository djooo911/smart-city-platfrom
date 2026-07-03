"""
Regression tests for POST /auth/login.
"""

import pytest
from tests.regression.conftest import TEST_USERS

from app.domain.entities.enums import Role

pytestmark = pytest.mark.regression


def test_login_with_valid_credentials_returns_token(client):
    username, password = TEST_USERS[Role.VIEWER]

    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["token_type"] == "bearer"
    assert len(body["data"]["access_token"]) > 0


def test_login_with_wrong_password_returns_401(client):
    username, _ = TEST_USERS[Role.VIEWER]

    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "wrong-password"}
    )

    assert response.status_code == 401


def test_login_with_unknown_username_returns_401(client):
    response = client.post(
        "/api/v1/auth/login", json={"username": "no-such-user", "password": "whatever"}
    )

    assert response.status_code == 401
