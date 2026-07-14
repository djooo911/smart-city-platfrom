"""
Shared pytest fixtures for the backend test suite.

A single fixture exposing a FastAPI TestClient. Because `main.py`'s
lifespan connects to MongoDB on startup, running these tests requires a
reachable Mongo instance (e.g. `docker-compose up mongo`, or the full
stack). This mirrors how the regression suite runs in CI (see
.github/workflows/ci.yml) — against a real MongoDB service container, not
a mock, to catch real integration issues.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client
