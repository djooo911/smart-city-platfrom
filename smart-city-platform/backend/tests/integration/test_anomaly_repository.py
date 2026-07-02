"""
Integration tests for MongoAnomalyRepository against a real MongoDB.
"""

from datetime import datetime

import pytest

from app.domain.entities.anomaly import Anomaly
from app.domain.entities.enums import AnomalySeverity, AnomalyType
from app.infrastructure.mongo.repositories.anomaly_repository import MongoAnomalyRepository

pytestmark = pytest.mark.integration


def _anomaly(**overrides) -> Anomaly:
    defaults = dict(
        device_id="lamp-test-001",
        type=AnomalyType.SENSOR_OUT_OF_RANGE,
        severity=AnomalySeverity.MEDIUM,
        detected_at=datetime(2026, 7, 3, 10, 0, 0),
        details={"ambient_light_pct": -5.0},
    )
    defaults.update(overrides)
    return Anomaly(**defaults)


async def test_save_and_list_by_device_round_trip(db):
    repository = MongoAnomalyRepository(db)
    anomaly = _anomaly()

    await repository.save(anomaly)
    result = await repository.list_by_device(anomaly.device_id)

    assert result == [anomaly]


async def test_raw_document_has_lifecycle_defaults_not_exposed_on_entity(db):
    repository = MongoAnomalyRepository(db)
    anomaly = _anomaly()
    await repository.save(anomaly)

    raw_doc = await db["anomalies"].find_one({"device_id": anomaly.device_id})

    assert raw_doc["resolved"] is False
    assert raw_doc["acknowledged_by"] is None
    assert raw_doc["blockchain_ref"] is None

    [entity] = await repository.list_by_device(anomaly.device_id)
    assert not hasattr(entity, "resolved")


async def test_list_by_device_orders_most_recent_first(db):
    repository = MongoAnomalyRepository(db)
    older = _anomaly(detected_at=datetime(2026, 7, 3, 9, 0, 0), type=AnomalyType.LAMP_OFFLINE)
    newer = _anomaly(
        detected_at=datetime(2026, 7, 3, 11, 0, 0), type=AnomalyType.ACTUATOR_MISMATCH
    )

    await repository.save(older)
    await repository.save(newer)

    result = await repository.list_by_device(older.device_id)

    assert result == [newer, older]


async def test_list_by_device_scoped_to_device_id(db):
    repository = MongoAnomalyRepository(db)
    await repository.save(_anomaly(device_id="lamp-test-a"))
    await repository.save(_anomaly(device_id="lamp-test-b"))

    result = await repository.list_by_device("lamp-test-a")

    assert len(result) == 1
    assert result[0].device_id == "lamp-test-a"
