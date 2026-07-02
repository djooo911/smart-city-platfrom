"""
Anomaly entity.

The result of a domain rule detecting a problem (see
domain/rules/anomaly_detection.py). Deliberately a subset of the persisted
`anomalies` document in docs/architecture.md §6.4: `resolved`,
`acknowledged_by`, and `blockchain_ref` are workflow/lifecycle fields owned
by later milestones (M3 repository, M4 API), not part of the detection
result itself.
"""

from dataclasses import dataclass
from datetime import datetime

from app.domain.entities.enums import AnomalySeverity, AnomalyType


@dataclass(frozen=True)
class Anomaly:
    device_id: str
    type: AnomalyType
    severity: AnomalySeverity
    detected_at: datetime
    details: dict
