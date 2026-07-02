"""
MongoLampRepository — Mongo-backed implementation of LampRepository.

Two mapping asymmetries vs. the domain entity, both deliberate and
confined to this file:

1. `_id` is the device_id string (per docs/architecture.md §6.2), not an
   ObjectId. `upsert` builds the replacement document WITHOUT an `_id`
   key and relies on `replace_one`'s filter to populate it on insert --
   passing a mismatched `_id` inside the replacement document itself
   would raise an error.
2. `LampConfig`'s 4 flat domain fields map to a nested document shape
   (`min_brightness`/`max_brightness` at the top of `config`, the other
   two nested under `anomaly_thresholds`) matching architecture.md's
   documented schema. `location` and `firmware_version` exist in that
   schema but have no home in the domain entities yet -- they're simply
   omitted from the write payload (no null placeholders) until a later
   milestone populates them meaningfully.

Enums are serialized via explicit `.value` / reconstructed via the enum
constructor rather than relying on implicit BSON string coercion.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.entities.enums import LampStatus
from app.domain.entities.lamp_config import LampConfig
from app.domain.entities.lamp_node import LampNode

_COLLECTION_NAME = "lamp_nodes"


def _config_to_document(config: LampConfig) -> dict:
    return {
        "min_brightness": config.min_brightness_pct,
        "max_brightness": config.max_brightness_pct,
        "anomaly_thresholds": {
            "offline_timeout_seconds": config.offline_timeout_seconds,
            "actuator_mismatch_tolerance_pct": config.actuator_mismatch_tolerance_pct,
        },
    }


def _config_from_document(doc: dict) -> LampConfig:
    thresholds = doc["anomaly_thresholds"]
    return LampConfig(
        min_brightness_pct=doc["min_brightness"],
        max_brightness_pct=doc["max_brightness"],
        offline_timeout_seconds=thresholds["offline_timeout_seconds"],
        actuator_mismatch_tolerance_pct=thresholds["actuator_mismatch_tolerance_pct"],
    )


def _to_document(lamp: LampNode) -> dict:
    return {
        "status": lamp.status.value,
        "current_brightness_pct": lamp.current_brightness_pct,
        "last_seen": lamp.last_seen,
        "config": _config_to_document(lamp.config),
    }


def _to_entity(doc: dict) -> LampNode:
    return LampNode(
        device_id=doc["_id"],
        status=LampStatus(doc["status"]),
        current_brightness_pct=doc["current_brightness_pct"],
        last_seen=doc["last_seen"],
        config=_config_from_document(doc["config"]),
    )


class MongoLampRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db[_COLLECTION_NAME]

    async def upsert(self, lamp: LampNode) -> None:
        await self._collection.replace_one(
            {"_id": lamp.device_id}, _to_document(lamp), upsert=True
        )

    async def get(self, device_id: str) -> LampNode | None:
        doc = await self._collection.find_one({"_id": device_id})
        return _to_entity(doc) if doc else None

    async def list_all(self) -> list[LampNode]:
        return [_to_entity(doc) async for doc in self._collection.find({})]
