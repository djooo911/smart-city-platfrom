"""
Shared pytest fixtures for the backend test suite.

Milestone 0 scope: a single fixture exposing a FastAPI TestClient. Because
`main.py`'s lifespan connects to MongoDB on startup, running these tests
requires a reachable Mongo instance (e.g. `docker-compose up mongo`, or the
full stack). This mirrors how the regression suite will run in CI (see
ci/github-actions/regression-tests.yml, added in Milestone 8) — against a
real MongoDB service container, not a mock, to catch real integration
issues.

Future milestones will add fixtures for: a clean test database per test
run, seeded fixture data, and a blockchain fixture pre-populated with a
known-valid chain.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client
