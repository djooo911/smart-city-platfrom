"""
Seed script — populates a fresh database with sample data for manual
exploration and demos. Idempotent: upserts lamp nodes (safe to re-run),
only creates a genesis blockchain if the `blockchain` collection is empty,
and only creates the admin/device users if they don't already exist.

Run standalone from `backend/`:
    python -m app.infrastructure.mongo.seed

Requires ADMIN_SEED_PASSWORD / DEVICE_SEED_PASSWORD to be set (see
backend/.env.example) to seed the respective user -- each is skipped
(with a logged warning, not a guessable default) if its password is unset.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.config import get_settings
from app.domain.entities.enums import LampStatus, Role
from app.domain.entities.lamp_config import LampConfig
from app.domain.entities.lamp_node import LampNode
from app.domain.entities.location import Location
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
_DEVICE_USERNAME = "lamp-device"

_SAMPLE_LAMPS = [
    LampNode(
        device_id="lamp-001",
        status=LampStatus.ONLINE,
        current_brightness_pct=50.0,
        last_seen=datetime.now(timezone.utc).replace(tzinfo=None),
        config=LampConfig(),
        location=Location(lat=36.8065, lng=10.1815, label="Avenue Habib Bourguiba"),
    ),
    LampNode(
        device_id="lamp-002",
        status=LampStatus.ONLINE,
        current_brightness_pct=75.0,
        last_seen=datetime.now(timezone.utc).replace(tzinfo=None),
        config=LampConfig(),
        location=Location(lat=36.8189, lng=10.1658, label="Rue de Marseille"),
    ),
    LampNode(
        device_id="lamp-003",
        status=LampStatus.OFFLINE,
        current_brightness_pct=0.0,
        last_seen=datetime.now(timezone.utc).replace(tzinfo=None),
        config=LampConfig(),
        location=Location(lat=36.7990, lng=10.1950, label="Avenue Mohamed V"),
    ),
    LampNode(
        device_id="lamp-004",
        status=LampStatus.ONLINE,
        current_brightness_pct=60.0,
        last_seen=datetime.now(timezone.utc).replace(tzinfo=None),
        config=LampConfig(),
        location=Location(lat=36.8034, lng=10.1750, label="Avenue de Paris"),
    ),
    LampNode(
        device_id="lamp-005",
        status=LampStatus.ONLINE,
        current_brightness_pct=45.0,
        last_seen=datetime.now(timezone.utc).replace(tzinfo=None),
        config=LampConfig(),
        location=Location(lat=36.8102, lng=10.1739, label="Avenue de la Liberté"),
    ),
    LampNode(
        device_id="lamp-006",
        status=LampStatus.OFFLINE,
        current_brightness_pct=0.0,
        last_seen=datetime.now(timezone.utc).replace(tzinfo=None),
        config=LampConfig(),
        location=Location(lat=36.8058, lng=10.1699, label="Rue de Palestine"),
    ),
]


async def _seed_user(
    user_repository: MongoUserRepository, username: str, password: str | None, role: Role
) -> None:
    if await user_repository.get_by_username(username) is not None:
        logger.info("User %r already exists, skipping", username)
    elif not password:
        logger.warning("Password not set for %r -- skipping user creation", username)
    else:
        await user_repository.create(
            User(username=username, password_hash=hash_password(password), role=role)
        )
        logger.info("Created user %r (%s)", username, role.value)


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

    settings = get_settings()
    user_repository = MongoUserRepository(db)
    await _seed_user(user_repository, _ADMIN_USERNAME, settings.admin_seed_password, Role.ADMIN)
    await _seed_user(
        user_repository, _DEVICE_USERNAME, settings.device_seed_password, Role.OPERATOR
    )


async def _main() -> None:
    configure_logging()
    connect_to_mongo()
    try:
        await seed(get_database())
    finally:
        close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(_main())
