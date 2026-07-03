"""
MongoAnomalyRepository — Mongo-backed implementation of AnomalyRepository.

Now that the Anomaly entity carries `resolved`/`acknowledged_by`/
`blockchain_ref` directly (Milestone 4), `_to_document`/`_to_entity` are a
genuine 1:1 mapping — no more injecting untracked defaults behind the
entity's back, as M3 had to do before this milestone gave those fields a
caller. `_id` is a Mongo ObjectId; `get_by_id`/`mark_acknowledged`/
`set_blockchain_ref` all take the string form and convert.
"""

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.entities.anomaly import Anomaly
from app.domain.entities.enums import AnomalySeverity, AnomalyType

_COLLECTION_NAME = "anomalies"


def _to_document(anomaly: Anomaly) -> dict:
    return {
        "device_id": anomaly.device_id,
        "type": anomaly.type.value,
        "severity": anomaly.severity.value,
        "detected_at": anomaly.detected_at,
        "details": anomaly.details,
        "resolved": anomaly.resolved,
        "acknowledged_by": anomaly.acknowledged_by,
        "blockchain_ref": anomaly.blockchain_ref,
    }


def _to_entity(doc: dict) -> Anomaly:
    return Anomaly(
        device_id=doc["device_id"],
        type=AnomalyType(doc["type"]),
        severity=AnomalySeverity(doc["severity"]),
        detected_at=doc["detected_at"],
        details=doc["details"],
        id=str(doc["_id"]),
        resolved=doc["resolved"],
        acknowledged_by=doc["acknowledged_by"],
        blockchain_ref=doc["blockchain_ref"],
    )


class MongoAnomalyRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db[_COLLECTION_NAME]

    async def save(self, anomaly: Anomaly) -> str:
        result = await self._collection.insert_one(_to_document(anomaly))
        return str(result.inserted_id)

    async def list_by_device(self, device_id: str) -> list[Anomaly]:
        cursor = self._collection.find({"device_id": device_id}).sort("detected_at", -1)
        return [_to_entity(doc) async for doc in cursor]

    async def list_all(
        self,
        device_id: str | None = None,
        resolved: bool | None = None,
        severity: AnomalySeverity | None = None,
    ) -> list[Anomaly]:
        query: dict = {}
        if device_id is not None:
            query["device_id"] = device_id
        if resolved is not None:
            query["resolved"] = resolved
        if severity is not None:
            query["severity"] = severity.value

        cursor = self._collection.find(query).sort("detected_at", -1)
        return [_to_entity(doc) async for doc in cursor]

    async def get_by_id(self, anomaly_id: str) -> Anomaly | None:
        doc = await self._collection.find_one({"_id": ObjectId(anomaly_id)})
        return _to_entity(doc) if doc else None

    async def mark_acknowledged(self, anomaly_id: str, acknowledged_by: str) -> None:
        await self._collection.update_one(
            {"_id": ObjectId(anomaly_id)},
            {"$set": {"resolved": True, "acknowledged_by": acknowledged_by}},
        )

    async def set_blockchain_ref(self, anomaly_id: str, block_hash: str) -> None:
        await self._collection.update_one(
            {"_id": ObjectId(anomaly_id)}, {"$set": {"blockchain_ref": block_hash}}
        )
