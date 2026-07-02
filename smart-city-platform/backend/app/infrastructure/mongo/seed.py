"""
Seed script — populates a fresh database with sample data for manual
exploration and demos. Idempotent: upserts lamp nodes (safe to re-run) and
only creates a genesis blockchain if the `blockchain` collection is empty.

Run standalone from `backend/`:
    python -m app.infrastructure.mongo.seed
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.domain.entities.enums import LampStatus
from app.domain.entities.lamp_config import LampConfig
from app.domain.entities.lamp_node import LampNode
from app.infrastructure.blockchain.chain import create_genesis_chain
from app.infrastructure.mongo.client import close_mongo_connection, connect_to_mongo, get_database
from app.infrastructure.mongo.indexes import ensure_indexes
from app.infrastructure.mongo.repositories.blockchain_repository import MongoBlockchainRepository
from app.infrastructure.mongo.repositories.lamp_repository import MongoLampRepository
from app.logging_config import configure_logging
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

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


async def _main() -> None:
    configure_logging()
    connect_to_mongo()
    try:
        await seed(get_database())
    finally:
        close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(_main())
