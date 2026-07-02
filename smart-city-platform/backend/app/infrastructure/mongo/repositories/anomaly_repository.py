"""
MongoAnomalyRepository — Mongo-backed implementation of AnomalyRepository.

The persisted `anomalies` document (docs/architecture.md §6.4) has three
lifecycle fields -- resolved, acknowledged_by, blockchain_ref -- that the
Anomaly domain entity deliberately does not model (see its docstring: a
detection result is not the same thing as its acknowledgement workflow
state). `_to_document` materializes sane defaults for those fields on
every new anomaly; `_to_entity` reads back only the 5 domain fields and
ignores the rest. This is what makes architecture.md's
(device_id, resolved, severity) compound index meaningful even though
`resolved` isn't part of the entity itself.
"""

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
        "resolved": False,
        "acknowledged_by": None,
        "blockchain_ref": None,
    }


def _to_entity(doc: dict) -> Anomaly:
    return Anomaly(
        device_id=doc["device_id"],
        type=AnomalyType(doc["type"]),
        severity=AnomalySeverity(doc["severity"]),
        detected_at=doc["detected_at"],
        details=doc["details"],
    )


class MongoAnomalyRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db[_COLLECTION_NAME]

    async def save(self, anomaly: Anomaly) -> None:
        await self._collection.insert_one(_to_document(anomaly))

    async def list_by_device(self, device_id: str) -> list[Anomaly]:
        cursor = self._collection.find({"device_id": device_id}).sort("detected_at", -1)
        return [_to_entity(doc) async for doc in cursor]
