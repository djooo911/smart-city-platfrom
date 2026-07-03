"""
Integration tests for MongoAnomalyRepository against a real MongoDB.

Updated for Milestone 4: `save` now returns the new document's id, and
the Anomaly entity itself carries `id`/`resolved`/`acknowledged_by`/
`blockchain_ref` (Milestone 1/3 deliberately deferred these -- see
Anomaly's docstring -- until M4's alert-acknowledgement endpoint and
blockchain-linking gave them a caller).
"""

import dataclasses
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

    anomaly_id = await repository.save(anomaly)
    result = await repository.list_by_device(anomaly.device_id)

    assert result == [dataclasses.replace(anomaly, id=anomaly_id)]


async def test_saved_anomaly_has_lifecycle_defaults(db):
    repository = MongoAnomalyRepository(db)
    anomaly = _anomaly()
    anomaly_id = await repository.save(anomaly)

    raw_doc = await db["anomalies"].find_one({"device_id": anomaly.device_id})
    assert raw_doc["resolved"] is False
    assert raw_doc["acknowledged_by"] is None
    assert raw_doc["blockchain_ref"] is None

    [entity] = await repository.list_by_device(anomaly.device_id)
    assert entity.id == anomaly_id
    assert entity.resolved is False
    assert entity.acknowledged_by is None
    assert entity.blockchain_ref is None


async def test_list_by_device_orders_most_recent_first(db):
    repository = MongoAnomalyRepository(db)
    older = _anomaly(detected_at=datetime(2026, 7, 3, 9, 0, 0), type=AnomalyType.LAMP_OFFLINE)
    newer = _anomaly(
        detected_at=datetime(2026, 7, 3, 11, 0, 0), type=AnomalyType.ACTUATOR_MISMATCH
    )

    await repository.save(older)
    await repository.save(newer)

    result = await repository.list_by_device(older.device_id)

    assert [a.type for a in result] == [newer.type, older.type]


async def test_list_by_device_scoped_to_device_id(db):
    repository = MongoAnomalyRepository(db)
    await repository.save(_anomaly(device_id="lamp-test-a"))
    await repository.save(_anomaly(device_id="lamp-test-b"))

    result = await repository.list_by_device("lamp-test-a")

    assert len(result) == 1
    assert result[0].device_id == "lamp-test-a"


async def test_get_by_id_returns_matching_anomaly(db):
    repository = MongoAnomalyRepository(db)
    anomaly_id = await repository.save(_anomaly())

    result = await repository.get_by_id(anomaly_id)

    assert result is not None
    assert result.id == anomaly_id


async def test_get_by_id_returns_none_for_unknown_id(db):
    repository = MongoAnomalyRepository(db)

    assert await repository.get_by_id("000000000000000000000000") is None


async def test_mark_acknowledged_sets_resolved_and_acknowledged_by(db):
    repository = MongoAnomalyRepository(db)
    anomaly_id = await repository.save(_anomaly())

    await repository.mark_acknowledged(anomaly_id, "operator1")

    result = await repository.get_by_id(anomaly_id)
    assert result.resolved is True
    assert result.acknowledged_by == "operator1"


async def test_set_blockchain_ref(db):
    repository = MongoAnomalyRepository(db)
    anomaly_id = await repository.save(_anomaly())

    await repository.set_blockchain_ref(anomaly_id, "0" * 64)

    result = await repository.get_by_id(anomaly_id)
    assert result.blockchain_ref == "0" * 64


async def test_list_all_filters_by_resolved_and_severity(db):
    repository = MongoAnomalyRepository(db)
    device_id = "lamp-test-filter"
    low = await repository.save(
        _anomaly(device_id=device_id, severity=AnomalySeverity.LOW)
    )
    await repository.save(_anomaly(device_id=device_id, severity=AnomalySeverity.HIGH))
    await repository.mark_acknowledged(low, "operator1")

    unresolved = await repository.list_all(device_id=device_id, resolved=False)
    assert all(a.resolved is False for a in unresolved)

    low_severity = await repository.list_all(device_id=device_id, severity=AnomalySeverity.LOW)
    assert all(a.severity == AnomalySeverity.LOW for a in low_severity)
