"""
Shared fixtures for repository integration tests.

These connect directly to Mongo via Motor -- bypassing the FastAPI app
entirely -- since they exercise the repository layer, not the API.

Safety guard: refuses to run against `mongo_db_name == "smart_city_db"`
(the Render production database name). Tests here drop collections at
teardown, so accidentally pointing a local .env at production would be
destructive. See backend/.env.example for the expected local setup
(same Atlas cluster, different db name).
"""

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.infrastructure.mongo.indexes import ensure_indexes

_COLLECTIONS_TO_RESET = ["lamp_nodes", "sensor_readings", "anomalies", "blockchain"]


@pytest.fixture
async def db():
    settings = get_settings()
    if settings.mongo_db_name == "smart_city_db":
        raise RuntimeError(
            "Refusing to run integration tests against 'smart_city_db' "
            "(the production database name). Set MONGO_DB_NAME to something "
            "else (e.g. 'smart_city_test') in backend/.env -- see "
            "backend/.env.example."
        )

    client = AsyncIOMotorClient(settings.mongo_uri)
    database = client[settings.mongo_db_name]
    await ensure_indexes(database)

    yield database

    for collection_name in _COLLECTIONS_TO_RESET:
        await database[collection_name].delete_many({})
    client.close()
