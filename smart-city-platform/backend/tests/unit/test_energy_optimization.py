"""
Unit tests for the energy optimization rule. Pure logic, no infra: does
not use the `client` fixture from conftest.py, so it runs without Mongo.
"""

from datetime import datetime

import pytest

from app.domain.entities.lamp_config import LampConfig
from app.domain.entities.sensor_reading import SensorReading
from app.domain.rules.energy_optimization import compute_target_brightness

pytestmark = pytest.mark.unit

DAY = datetime(2026, 7, 2, 14, 0, 0)  # 14:00, clearly outside the night window
NIGHT = datetime(2026, 7, 2, 2, 30, 0)  # 02:30, inside the night window


def _reading(**overrides) -> SensorReading:
    defaults = dict(
        device_id="lamp-001",
        timestamp=DAY,
        ambient_light_pct=50.0,
        pir_triggered=False,
        distance_cm=None,
        vehicle_detected=False,
        led_brightness_pct=50.0,
    )
    defaults.update(overrides)
    return SensorReading(**defaults)


def test_idle_daytime_dims_to_half_of_base():
    reading = _reading(ambient_light_pct=50.0)
    config = LampConfig()

    result = compute_target_brightness(reading, config, DAY)

    # base = 100 - 50 = 50; idle factor 0.5 -> 25
    assert result == pytest.approx(25.0)


def test_pir_presence_boosts_brightness_regardless_of_ambient_light():
    reading = _reading(ambient_light_pct=90.0, pir_triggered=True)
    config = LampConfig()

    result = compute_target_brightness(reading, config, DAY)

    # base = 10, but presence forces at least 90
    assert result == pytest.approx(90.0)


def test_vehicle_presence_boosts_brightness():
    reading = _reading(ambient_light_pct=90.0, vehicle_detected=True)
    config = LampConfig()

    result = compute_target_brightness(reading, config, DAY)

    assert result == pytest.approx(90.0)


def test_presence_with_low_ambient_light_uses_base_when_higher_than_boost():
    reading = _reading(ambient_light_pct=0.0, pir_triggered=True)
    config = LampConfig()

    result = compute_target_brightness(reading, config, DAY)

    # base = 100, which is already above the 90 presence floor
    assert result == pytest.approx(100.0)


def test_night_window_applies_extra_idle_discount():
    reading = _reading(ambient_light_pct=50.0)
    config = LampConfig()

    result = compute_target_brightness(reading, config, NIGHT)

    # base = 50; idle 0.5 -> 25; night factor 0.7 -> 17.5
    assert result == pytest.approx(17.5)


def test_night_window_does_not_affect_presence_boost():
    reading = _reading(ambient_light_pct=90.0, pir_triggered=True)
    config = LampConfig()

    result = compute_target_brightness(reading, config, NIGHT)

    assert result == pytest.approx(90.0)


def test_result_clamped_to_custom_max_brightness():
    reading = _reading(ambient_light_pct=0.0, pir_triggered=True)
    config = LampConfig(max_brightness_pct=80.0)

    result = compute_target_brightness(reading, config, DAY)

    assert result == pytest.approx(80.0)


def test_result_clamped_to_custom_min_brightness():
    reading = _reading(ambient_light_pct=100.0)
    config = LampConfig(min_brightness_pct=20.0)

    result = compute_target_brightness(reading, config, DAY)

    # base = 0 -> idle brightness 0, clamped up to the configured minimum
    assert result == pytest.approx(20.0)


def test_ambient_light_boundary_zero():
    reading = _reading(ambient_light_pct=0.0)
    config = LampConfig()

    result = compute_target_brightness(reading, config, DAY)

    assert result == pytest.approx(50.0)


def test_ambient_light_boundary_hundred():
    reading = _reading(ambient_light_pct=100.0)
    config = LampConfig()

    result = compute_target_brightness(reading, config, DAY)

    # base = 0 -> idle brightness 0, floored to the default min_brightness_pct
    assert result == pytest.approx(config.min_brightness_pct)


def test_out_of_range_ambient_light_is_defensively_clamped():
    reading = _reading(ambient_light_pct=150.0)
    config = LampConfig()

    result = compute_target_brightness(reading, config, DAY)

    # clamped to 100 -> base 0 -> idle brightness 0, then floored to config min
    assert result == pytest.approx(config.min_brightness_pct)


def test_negative_ambient_light_is_defensively_clamped():
    reading = _reading(ambient_light_pct=-20.0)
    config = LampConfig()

    result = compute_target_brightness(reading, config, DAY)

    # clamped to 0 -> base 100 -> idle brightness 50
    assert result == pytest.approx(50.0)


def test_night_window_start_boundary_is_inclusive():
    reading = _reading(ambient_light_pct=50.0)
    config = LampConfig()

    result = compute_target_brightness(reading, config, datetime(2026, 7, 2, 0, 0, 0))

    assert result == pytest.approx(17.5)


def test_night_window_end_boundary_is_exclusive():
    reading = _reading(ambient_light_pct=50.0)
    config = LampConfig()

    result = compute_target_brightness(reading, config, datetime(2026, 7, 2, 5, 0, 0))

    assert result == pytest.approx(25.0)
