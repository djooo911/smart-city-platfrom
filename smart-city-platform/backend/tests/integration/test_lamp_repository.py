"""
Integration tests for MongoLampRepository against a real MongoDB.
"""

from datetime import datetime

import pytest

from app.domain.entities.enums import LampStatus
from app.domain.entities.lamp_config import LampConfig
from app.domain.entities.lamp_node import LampNode
from app.infrastructure.mongo.repositories.lamp_repository import MongoLampRepository

pytestmark = pytest.mark.integration

NOW = datetime(2026, 7, 3, 10, 0, 0)


def _lamp(**overrides) -> LampNode:
    defaults = dict(
        device_id="lamp-test-001",
        status=LampStatus.ONLINE,
        current_brightness_pct=42.0,
        last_seen=NOW,
        config=LampConfig(
            min_brightness_pct=5.0,
            max_brightness_pct=95.0,
            offline_timeout_seconds=120,
            actuator_mismatch_tolerance_pct=20.0,
        ),
    )
    defaults.update(overrides)
    return LampNode(**defaults)


async def test_upsert_and_get_round_trip(db):
    repository = MongoLampRepository(db)
    lamp = _lamp()

    await repository.upsert(lamp)
    result = await repository.get(lamp.device_id)

    assert result == lamp


async def test_config_nested_mapping_survives_round_trip(db):
    repository = MongoLampRepository(db)
    lamp = _lamp(config=LampConfig(min_brightness_pct=1.0, max_brightness_pct=99.0))

    await repository.upsert(lamp)
    result = await repository.get(lamp.device_id)

    assert result.config == lamp.config


async def test_get_returns_none_for_unknown_device_id(db):
    repository = MongoLampRepository(db)

    assert await repository.get("does-not-exist") is None


async def test_upsert_updates_existing_lamp(db):
    repository = MongoLampRepository(db)
    lamp = _lamp(current_brightness_pct=10.0)
    await repository.upsert(lamp)

    updated = _lamp(current_brightness_pct=80.0, status=LampStatus.OFFLINE)
    await repository.upsert(updated)

    result = await repository.get(lamp.device_id)
    assert result.current_brightness_pct == 80.0
    assert result.status == LampStatus.OFFLINE


async def test_list_all_returns_every_lamp(db):
    repository = MongoLampRepository(db)
    await repository.upsert(_lamp(device_id="lamp-test-a"))
    await repository.upsert(_lamp(device_id="lamp-test-b"))

    result = await repository.list_all()

    device_ids = {lamp.device_id for lamp in result}
    assert {"lamp-test-a", "lamp-test-b"}.issubset(device_ids)
