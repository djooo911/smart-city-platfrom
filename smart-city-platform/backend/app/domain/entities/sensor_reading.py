"""
SensorReading entity.

A single telemetry sample from a lamp node. Fields map directly to the
`sensor_readings` collection described in docs/architecture.md §6.1.

This is a pure data holder: it does not validate that percentages are in
range or that `distance_cm` is physically plausible. That validation is a
business rule (see domain/rules/anomaly_detection.py), not an entity
invariant — keeping it out of the entity means the anomaly detector can
observe and report on invalid readings instead of the entity refusing to
even represent them.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SensorReading:
    device_id: str
    timestamp: datetime
    ambient_light_pct: float
    pir_triggered: bool
    distance_cm: float | None
    vehicle_detected: bool
    led_brightness_pct: float
