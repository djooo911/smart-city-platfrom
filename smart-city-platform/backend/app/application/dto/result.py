"""
Small result DTOs for use cases whose return shape is richer than a
single entity.
"""

from dataclasses import dataclass

from app.domain.entities.anomaly import Anomaly


@dataclass(frozen=True)
class IngestTelemetryResult:
    brightness_pct: float
    anomalies: list[Anomaly]
