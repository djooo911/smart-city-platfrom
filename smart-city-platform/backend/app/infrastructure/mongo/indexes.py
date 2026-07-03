"""
Index creation, matching docs/architecture.md §6.7 exactly.

`create_index` is idempotent (a no-op if an equivalent index already
exists), so `ensure_indexes` is safe to call on every app startup
(app/main.py's lifespan) and from the integration test fixture alike.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db["sensor_readings"].create_index([("device_id", 1), ("timestamp", 1)])

    await db["anomalies"].create_index([("device_id", 1), ("resolved", 1), ("severity", 1)])

    await db["blockchain"].create_index("index", unique=True)
    await db["blockchain"].create_index("hash")
    await db["blockchain"].create_index("data.device_id")
