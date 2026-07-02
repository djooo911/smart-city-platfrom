"""
MongoDB connection management.

This module owns the single Motor (async MongoDB driver) client instance
for the whole application. It is intentionally the *only* place in the
infrastructure layer that knows how to open/close a database connection.

Repository implementations (added in Milestone 3, e.g.
`infrastructure/mongo/repositories/lamp_repository.py`) will depend on
`get_database()` rather than importing Motor directly elsewhere in the
codebase. This keeps the dependency on "MongoDB specifically" contained
to the infrastructure layer, consistent with the Clean Architecture
boundary described in the architecture document.

Milestone 0 scope: connection setup + a `ping` used by the health check
endpoint only. No collections, schemas, or repositories yet.
"""

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


def connect_to_mongo() -> None:
    """Initialize the Mongo client. Called once on application startup."""
    global _client
    settings = get_settings()
    logger.info("Connecting to MongoDB at %s", settings.mongo_uri)
    _client = AsyncIOMotorClient(settings.mongo_uri)


def close_mongo_connection() -> None:
    """Close the Mongo client. Called once on application shutdown."""
    global _client
    if _client is not None:
        logger.info("Closing MongoDB connection")
        _client.close()
        _client = None


def get_database() -> AsyncIOMotorDatabase:
    """
    Return the application's database handle.

    Raises a RuntimeError if called before `connect_to_mongo()` has run
    (i.e. outside the FastAPI lifespan), which is preferable to silently
    returning None and failing later with a confusing AttributeError.
    """
    if _client is None:
        raise RuntimeError(
            "MongoDB client is not initialized. "
            "connect_to_mongo() must be called during app startup."
        )
    settings = get_settings()
    return _client[settings.mongo_db_name]


async def ping_database() -> bool:
    """Used by the /system/health endpoint to verify DB connectivity."""
    try:
        db = get_database()
        await db.command("ping")
        return True
    except Exception:
        logger.exception("MongoDB ping failed")
        return False
