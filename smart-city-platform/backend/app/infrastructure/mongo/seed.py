"""
Seed script — populates a fresh database with sample data for manual
exploration and demos. Idempotent: upserts lamp nodes (safe to re-run),
only creates a genesis blockchain if the `blockchain` collection is empty,
and only creates the default admin user if one doesn't already exist.

Run standalone from `backend/`:
    python -m app.infrastructure.mongo.seed

Requires ADMIN_SEED_PASSWORD to be set (see backend/.env.example) --
fails loudly rather than falling back to a guessable default password.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.config import get_settings
from app.domain.entities.enums import LampStatus, Role
from app.domain.entities.lamp_config import LampConfig
from app.domain.entities.lamp_node import LampNode
from app.domain.entities.user import User
from app.infrastructure.blockchain.chain import create_genesis_chain
from app.infrastructure.mongo.client import close_mongo_connection, connect_to_mongo, get_database
from app.infrastructure.mongo.indexes import ensure_indexes
from app.infrastructure.mongo.repositories.blockchain_repository import MongoBlockchainRepository
from app.infrastructure.mongo.repositories.lamp_repository import MongoLampRepository
from app.infrastructure.mongo.repositories.user_repository import MongoUserRepository
from app.logging_config import configure_logging
from app.security.password import hash_password
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

_ADMIN_USERNAME = "admin"

_SAMPLE_LAMPS = [
    LampNode(
        device_id="lamp-001",
        status=LampStatus.ONLINE,
        current_brightness_pct=50.0,
        last_seen=datetime.now(timezone.utc).replace(tzinfo=None),
        config=LampConfig(),
    ),
    LampNode(
        device_id="lamp-002",
        status=LampStatus.ONLINE,
        current_brightness_pct=75.0,
        last_seen=datetime.now(timezone.utc).replace(tzinfo=None),
        config=LampConfig(),
    ),
    LampNode(
        device_id="lamp-003",
        status=LampStatus.OFFLINE,
        current_brightness_pct=0.0,
        last_seen=datetime.now(timezone.utc).replace(tzinfo=None),
        config=LampConfig(),
    ),
]


async def seed(db: AsyncIOMotorDatabase) -> None:
    await ensure_indexes(db)

    lamp_repository = MongoLampRepository(db)
    for lamp in _SAMPLE_LAMPS:
        await lamp_repository.upsert(lamp)
    logger.info("Seeded %d sample lamp nodes", len(_SAMPLE_LAMPS))

    blockchain_repository = MongoBlockchainRepository(db)
    existing_chain = await blockchain_repository.load_chain()
    if not existing_chain:
        genesis_chain = create_genesis_chain(datetime.now(timezone.utc).replace(tzinfo=None))
        await blockchain_repository.append_block(genesis_chain.latest_block)
        logger.info("Created genesis block")
    else:
        logger.info("Blockchain already has %d block(s), skipping genesis creation", len(existing_chain))

    admin_seed_password = get_settings().admin_seed_password
    user_repository = MongoUserRepository(db)
    if await user_repository.get_by_username(_ADMIN_USERNAME) is not None:
        logger.info("Admin user already exists, skipping")
    elif not admin_seed_password:
        logger.warning("ADMIN_SEED_PASSWORD not set -- skipping admin user creation")
    else:
        await user_repository.create(
            User(
                username=_ADMIN_USERNAME,
                password_hash=hash_password(admin_seed_password),
                role=Role.ADMIN,
            )
        )
        logger.info("Created default admin user %r", _ADMIN_USERNAME)


async def _main() -> None:
    configure_logging()
    connect_to_mongo()
    try:
        await seed(get_database())
    finally:
        close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(_main())
