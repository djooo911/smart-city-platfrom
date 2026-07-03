"""
Shared fixtures/helpers for regression tests.

Regression tests exercise the real HTTP surface end-to-end (via the
`client` fixture from tests/conftest.py, itself a plain FastAPI
TestClient -- no pytest-asyncio involved, since TestClient bridges
sync-to-async internally) against the real dev Atlas database. This file
adds a session-scoped fixture that seeds three known test users (one per
role) directly via the repository layer, and drops the relevant
collections once the whole regression suite finishes.

Each asyncio.run() call below creates and closes its OWN AsyncIOMotorClient
rather than sharing one across setup/teardown -- Motor's driver caches a
reference to the event loop it was first used on, so reusing a client
across two separate asyncio.run() calls (each of which gets a fresh loop)
raises "Event loop is closed" during the second call.
"""

import asyncio

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.domain.entities.enums import Role
from app.domain.entities.user import User
from app.infrastructure.mongo.repositories.user_repository import MongoUserRepository
from app.security.password import hash_password

_COLLECTIONS_TO_RESET = ["lamp_nodes", "sensor_readings", "anomalies", "blockchain", "users"]

TEST_USERS = {
    Role.ADMIN: ("regression-admin", "admin-pass-123"),
    Role.OPERATOR: ("regression-operator", "operator-pass-123"),
    Role.VIEWER: ("regression-viewer", "viewer-pass-123"),
}


@pytest.fixture(scope="session", autouse=True)
def seed_test_users():
    settings = get_settings()
    if settings.mongo_db_name == "smart_city_db":
        raise RuntimeError(
            "Refusing to run regression tests against 'smart_city_db' (production). "
            "Set MONGO_DB_NAME to something else in backend/.env."
        )

    async def _seed():
        client = AsyncIOMotorClient(settings.mongo_uri)
        try:
            db = client[settings.mongo_db_name]
            user_repository = MongoUserRepository(db)
            for role, (username, password) in TEST_USERS.items():
                if await user_repository.get_by_username(username) is None:
                    await user_repository.create(
                        User(username=username, password_hash=hash_password(password), role=role)
                    )
        finally:
            client.close()

    asyncio.run(_seed())

    yield

    async def _cleanup():
        client = AsyncIOMotorClient(settings.mongo_uri)
        try:
            db = client[settings.mongo_db_name]
            for name in _COLLECTIONS_TO_RESET:
                await db[name].delete_many({})
        finally:
            client.close()

    asyncio.run(_cleanup())


def auth_headers(client, role: Role) -> dict:
    username, password = TEST_USERS[role]
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
