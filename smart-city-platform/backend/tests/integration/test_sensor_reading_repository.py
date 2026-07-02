"""
Integration tests for MongoSensorReadingRepository against a real MongoDB.
"""

from datetime import datetime

import pytest

from app.domain.entities.sensor_reading import SensorReading
from app.infrastructure.mongo.repositories.sensor_reading_repository import (
    MongoSensorReadingRepository,
)

pytestmark = pytest.mark.integration


def _reading(**overrides) -> SensorReading:
    defaults = dict(
        device_id="lamp-test-001",
        timestamp=datetime(2026, 7, 3, 10, 0, 0),
        ambient_light_pct=40.0,
        pir_triggered=False,
        distance_cm=150.0,
        vehicle_detected=False,
        led_brightness_pct=60.0,
    )
    defaults.update(overrides)
    return SensorReading(**defaults)


async def test_save_and_get_latest_round_trip(db):
    repository = MongoSensorReadingRepository(db)
    reading = _reading()

    await repository.save(reading)
    result = await repository.get_latest(reading.device_id)

    assert result == reading


async def test_get_latest_returns_none_when_no_readings(db):
    repository = MongoSensorReadingRepository(db)

    assert await repository.get_latest("no-readings-device") is None


async def test_get_latest_returns_most_recent_reading_regardless_of_insert_order(db):
    repository = MongoSensorReadingRepository(db)
    older = _reading(timestamp=datetime(2026, 7, 3, 9, 0, 0), ambient_light_pct=20.0)
    newer = _reading(timestamp=datetime(2026, 7, 3, 11, 0, 0), ambient_light_pct=80.0)

    await repository.save(newer)
    await repository.save(older)

    result = await repository.get_latest(older.device_id)

    assert result == newer


async def test_get_latest_scoped_to_device_id(db):
    repository = MongoSensorReadingRepository(db)
    await repository.save(_reading(device_id="lamp-test-a", ambient_light_pct=10.0))
    await repository.save(_reading(device_id="lamp-test-b", ambient_light_pct=90.0))

    result = await repository.get_latest("lamp-test-a")

    assert result.device_id == "lamp-test-a"
    assert result.ambient_light_pct == 10.0
