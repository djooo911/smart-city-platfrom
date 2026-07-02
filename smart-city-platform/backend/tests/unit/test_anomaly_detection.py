"""
Unit tests for the anomaly detection rules. Pure logic, no infra: does not
use the `client` fixture from conftest.py, so it runs without Mongo.
"""

from datetime import datetime, timedelta

import pytest

from app.domain.entities.enums import AnomalyType, LampStatus
from app.domain.entities.lamp_config import LampConfig
from app.domain.entities.lamp_node import LampNode
from app.domain.entities.sensor_reading import SensorReading
from app.domain.rules.anomaly_detection import (
    detect_actuator_mismatch,
    detect_lamp_offline,
    detect_sensor_out_of_range,
    detect_traffic_spike,
)

pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 2, 14, 0, 0)


def _reading(**overrides) -> SensorReading:
    defaults = dict(
        device_id="lamp-001",
        timestamp=NOW,
        ambient_light_pct=50.0,
        pir_triggered=False,
        distance_cm=100.0,
        vehicle_detected=False,
        led_brightness_pct=50.0,
    )
    defaults.update(overrides)
    return SensorReading(**defaults)


def _lamp(**overrides) -> LampNode:
    defaults = dict(
        device_id="lamp-001",
        status=LampStatus.ONLINE,
        current_brightness_pct=50.0,
        last_seen=NOW,
        config=LampConfig(),
    )
    defaults.update(overrides)
    return LampNode(**defaults)


# --- detect_sensor_out_of_range -------------------------------------------------


def test_sensor_reading_within_range_is_not_an_anomaly():
    assert detect_sensor_out_of_range(_reading(), NOW) is None


def test_ambient_light_below_zero_is_an_anomaly():
    result = detect_sensor_out_of_range(_reading(ambient_light_pct=-1.0), NOW)

    assert result is not None
    assert result.type == AnomalyType.SENSOR_OUT_OF_RANGE
    assert "ambient_light_pct" in result.details["out_of_range_fields"]


def test_ambient_light_above_hundred_is_an_anomaly():
    result = detect_sensor_out_of_range(_reading(ambient_light_pct=101.0), NOW)

    assert result is not None
    assert "ambient_light_pct" in result.details["out_of_range_fields"]


def test_distance_none_is_not_an_anomaly():
    result = detect_sensor_out_of_range(_reading(distance_cm=None), NOW)

    assert result is None


def test_distance_above_range_is_an_anomaly():
    result = detect_sensor_out_of_range(_reading(distance_cm=401.0), NOW)

    assert result is not None
    assert "distance_cm" in result.details["out_of_range_fields"]


def test_led_brightness_out_of_range_is_an_anomaly():
    result = detect_sensor_out_of_range(_reading(led_brightness_pct=-5.0), NOW)

    assert result is not None
    assert "led_brightness_pct" in result.details["out_of_range_fields"]


def test_multiple_out_of_range_fields_are_all_reported():
    result = detect_sensor_out_of_range(
        _reading(ambient_light_pct=-1.0, led_brightness_pct=200.0), NOW
    )

    assert result is not None
    assert set(result.details["out_of_range_fields"]) == {
        "ambient_light_pct",
        "led_brightness_pct",
    }


def test_range_boundaries_are_inclusive_and_not_anomalies():
    result = detect_sensor_out_of_range(
        _reading(ambient_light_pct=0.0, distance_cm=400.0, led_brightness_pct=100.0), NOW
    )

    assert result is None


# --- detect_lamp_offline ---------------------------------------------------------


def test_lamp_within_timeout_is_not_offline():
    lamp = _lamp(last_seen=NOW - timedelta(seconds=30))

    assert detect_lamp_offline(lamp, NOW) is None


def test_lamp_past_timeout_is_offline():
    lamp = _lamp(last_seen=NOW - timedelta(seconds=61))

    result = detect_lamp_offline(lamp, NOW)

    assert result is not None
    assert result.type == AnomalyType.LAMP_OFFLINE


def test_lamp_exactly_at_timeout_is_not_offline():
    lamp = _lamp(last_seen=NOW - timedelta(seconds=60))

    assert detect_lamp_offline(lamp, NOW) is None


# --- detect_actuator_mismatch -----------------------------------------------------


def test_actuator_within_tolerance_is_not_an_anomaly():
    reading = _reading(led_brightness_pct=50.0)
    config = LampConfig()

    result = detect_actuator_mismatch(reading, commanded_brightness_pct=60.0, config=config, now=NOW)

    assert result is None


def test_actuator_beyond_tolerance_is_an_anomaly():
    reading = _reading(led_brightness_pct=50.0)
    config = LampConfig()

    result = detect_actuator_mismatch(reading, commanded_brightness_pct=70.0, config=config, now=NOW)

    assert result is not None
    assert result.type == AnomalyType.ACTUATOR_MISMATCH


def test_actuator_exactly_at_tolerance_is_not_an_anomaly():
    reading = _reading(led_brightness_pct=50.0)
    config = LampConfig(actuator_mismatch_tolerance_pct=15.0)

    result = detect_actuator_mismatch(reading, commanded_brightness_pct=65.0, config=config, now=NOW)

    assert result is None


# --- detect_traffic_spike ---------------------------------------------------------


def test_normal_traffic_is_not_a_spike():
    result = detect_traffic_spike("lamp-001", current_count=10, baseline_avg=5.0, now=NOW)

    assert result is None


def test_traffic_beyond_multiplier_is_a_spike():
    result = detect_traffic_spike("lamp-001", current_count=20, baseline_avg=5.0, now=NOW)

    assert result is not None
    assert result.type == AnomalyType.TRAFFIC_SPIKE


def test_traffic_exactly_at_multiplier_boundary_is_not_a_spike():
    result = detect_traffic_spike("lamp-001", current_count=15, baseline_avg=5.0, now=NOW)

    assert result is None


def test_cold_start_below_floor_is_not_a_spike():
    result = detect_traffic_spike("lamp-001", current_count=5, baseline_avg=0.0, now=NOW)

    assert result is None


def test_cold_start_above_floor_is_a_spike():
    result = detect_traffic_spike("lamp-001", current_count=11, baseline_avg=0.0, now=NOW)

    assert result is not None
    assert result.type == AnomalyType.TRAFFIC_SPIKE
