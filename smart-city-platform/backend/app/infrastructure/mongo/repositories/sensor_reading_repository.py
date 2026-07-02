"""
MongoSensorReadingRepository — Mongo-backed implementation of
SensorReadingRepository.

All SensorReading fields map 1:1 to the document (docs/architecture.md
§6.1) -- no asymmetries to reconcile here.

Note: architecture.md recommends a MongoDB *time-series collection* for
`sensor_readings`. That requires `create_collection(..., timeseries=...)`
before any insert and comes with real restrictions (limited index types,
non-idempotent "already exists" handling). Deferred as a documented scope
cut for Milestone 3 -- a regular collection with the compound
(device_id, timestamp) index (see infrastructure/mongo/indexes.py) is
sufficient at student-project data volumes.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.entities.sensor_reading import SensorReading

_COLLECTION_NAME = "sensor_readings"


def _to_document(reading: SensorReading) -> dict:
    return {
        "device_id": reading.device_id,
        "timestamp": reading.timestamp,
        "ambient_light_pct": reading.ambient_light_pct,
        "pir_triggered": reading.pir_triggered,
        "distance_cm": reading.distance_cm,
        "vehicle_detected": reading.vehicle_detected,
        "led_brightness_pct": reading.led_brightness_pct,
    }


def _to_entity(doc: dict) -> SensorReading:
    return SensorReading(
        device_id=doc["device_id"],
        timestamp=doc["timestamp"],
        ambient_light_pct=doc["ambient_light_pct"],
        pir_triggered=doc["pir_triggered"],
        distance_cm=doc["distance_cm"],
        vehicle_detected=doc["vehicle_detected"],
        led_brightness_pct=doc["led_brightness_pct"],
    )


class MongoSensorReadingRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db[_COLLECTION_NAME]

    async def save(self, reading: SensorReading) -> None:
        await self._collection.insert_one(_to_document(reading))

    async def get_latest(self, device_id: str) -> SensorReading | None:
        doc = await self._collection.find_one(
            {"device_id": device_id}, sort=[("timestamp", -1)]
        )
        return _to_entity(doc) if doc else None
