"""
Anomaly detection rules.

Four independent, pure functions — one per anomaly class defined in
docs/architecture.md §1.1 (G4). Each returns an `Anomaly` when its
condition is met, or `None` otherwise. `now` is always supplied by the
caller (never read from the system clock internally) so every rule stays
deterministic and unit-testable without mocking time.

Boundary convention: all thresholds are exclusive (a value exactly at the
limit is NOT an anomaly) — e.g. a lamp is only "offline" once elapsed time
strictly exceeds its timeout, not the instant it reaches it.
"""

from datetime import datetime

from app.domain.entities.anomaly import Anomaly
from app.domain.entities.enums import AnomalySeverity, AnomalyType
from app.domain.entities.lamp_config import LampConfig
from app.domain.entities.lamp_node import LampNode
from app.domain.entities.sensor_reading import SensorReading

_AMBIENT_LIGHT_RANGE = (0.0, 100.0)
_DISTANCE_RANGE_CM = (0.0, 400.0)
_BRIGHTNESS_RANGE = (0.0, 100.0)

# When there's no meaningful traffic history yet, a multiplier of a
# near-zero baseline would flag almost any activity. Use an absolute floor
# instead until real history accumulates.
_TRAFFIC_SPIKE_COLD_START_BASELINE = 1.0
_TRAFFIC_SPIKE_COLD_START_FLOOR = 10


def detect_sensor_out_of_range(reading: SensorReading, now: datetime) -> Anomaly | None:
    out_of_range_fields = {}

    if not (_AMBIENT_LIGHT_RANGE[0] <= reading.ambient_light_pct <= _AMBIENT_LIGHT_RANGE[1]):
        out_of_range_fields["ambient_light_pct"] = reading.ambient_light_pct

    if reading.distance_cm is not None and not (
        _DISTANCE_RANGE_CM[0] <= reading.distance_cm <= _DISTANCE_RANGE_CM[1]
    ):
        out_of_range_fields["distance_cm"] = reading.distance_cm

    if not (_BRIGHTNESS_RANGE[0] <= reading.led_brightness_pct <= _BRIGHTNESS_RANGE[1]):
        out_of_range_fields["led_brightness_pct"] = reading.led_brightness_pct

    if not out_of_range_fields:
        return None

    return Anomaly(
        device_id=reading.device_id,
        type=AnomalyType.SENSOR_OUT_OF_RANGE,
        severity=AnomalySeverity.MEDIUM,
        detected_at=now,
        details={"out_of_range_fields": out_of_range_fields},
    )


def detect_lamp_offline(lamp: LampNode, now: datetime) -> Anomaly | None:
    elapsed_seconds = (now - lamp.last_seen).total_seconds()

    if elapsed_seconds <= lamp.config.offline_timeout_seconds:
        return None

    return Anomaly(
        device_id=lamp.device_id,
        type=AnomalyType.LAMP_OFFLINE,
        severity=AnomalySeverity.HIGH,
        detected_at=now,
        details={
            "elapsed_seconds": elapsed_seconds,
            "timeout_seconds": lamp.config.offline_timeout_seconds,
        },
    )


def detect_actuator_mismatch(
    reading: SensorReading,
    commanded_brightness_pct: float,
    config: LampConfig,
    now: datetime,
) -> Anomaly | None:
    diff = abs(reading.led_brightness_pct - commanded_brightness_pct)

    if diff <= config.actuator_mismatch_tolerance_pct:
        return None

    return Anomaly(
        device_id=reading.device_id,
        type=AnomalyType.ACTUATOR_MISMATCH,
        severity=AnomalySeverity.MEDIUM,
        detected_at=now,
        details={
            "reported_brightness_pct": reading.led_brightness_pct,
            "commanded_brightness_pct": commanded_brightness_pct,
            "tolerance_pct": config.actuator_mismatch_tolerance_pct,
        },
    )


def detect_traffic_spike(
    device_id: str,
    current_count: int,
    baseline_avg: float,
    now: datetime,
    threshold_multiplier: float = 3.0,
) -> Anomaly | None:
    if baseline_avg < _TRAFFIC_SPIKE_COLD_START_BASELINE:
        is_spike = current_count > _TRAFFIC_SPIKE_COLD_START_FLOOR
    else:
        is_spike = current_count > baseline_avg * threshold_multiplier

    if not is_spike:
        return None

    return Anomaly(
        device_id=device_id,
        type=AnomalyType.TRAFFIC_SPIKE,
        severity=AnomalySeverity.LOW,
        detected_at=now,
        details={"current_count": current_count, "baseline_avg": baseline_avg},
    )
