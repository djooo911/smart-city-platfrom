"""
Entity -> response-dict serialization, shared across routers.

Kept separate from app/api/schemas/ (Pydantic request models) since these
build the plain-dict `{"data": ..., "meta": {}}` response bodies used
throughout the API (see system.py) rather than validating input.
"""

from app.domain.entities.anomaly import Anomaly
from app.domain.entities.lamp_node import LampNode
from app.domain.entities.sensor_reading import SensorReading
from app.infrastructure.blockchain.block import Block


def serialize_lamp(lamp: LampNode) -> dict:
    return {
        "device_id": lamp.device_id,
        "status": lamp.status.value,
        "current_brightness_pct": lamp.current_brightness_pct,
        "last_seen": lamp.last_seen.isoformat(),
        "config": {
            "min_brightness_pct": lamp.config.min_brightness_pct,
            "max_brightness_pct": lamp.config.max_brightness_pct,
            "offline_timeout_seconds": lamp.config.offline_timeout_seconds,
            "actuator_mismatch_tolerance_pct": lamp.config.actuator_mismatch_tolerance_pct,
        },
    }


def serialize_reading(reading: SensorReading) -> dict:
    return {
        "device_id": reading.device_id,
        "timestamp": reading.timestamp.isoformat(),
        "ambient_light_pct": reading.ambient_light_pct,
        "pir_triggered": reading.pir_triggered,
        "distance_cm": reading.distance_cm,
        "vehicle_detected": reading.vehicle_detected,
        "led_brightness_pct": reading.led_brightness_pct,
    }


def serialize_anomaly(anomaly: Anomaly) -> dict:
    return {
        "id": anomaly.id,
        "device_id": anomaly.device_id,
        "type": anomaly.type.value,
        "severity": anomaly.severity.value,
        "detected_at": anomaly.detected_at.isoformat(),
        "details": anomaly.details,
        "resolved": anomaly.resolved,
        "acknowledged_by": anomaly.acknowledged_by,
        "blockchain_ref": anomaly.blockchain_ref,
    }


def serialize_block(block: Block) -> dict:
    return {
        "index": block.index,
        "timestamp": block.timestamp.isoformat(),
        "data": block.data,
        "previous_hash": block.previous_hash,
        "nonce": block.nonce,
        "hash": block.hash,
    }
