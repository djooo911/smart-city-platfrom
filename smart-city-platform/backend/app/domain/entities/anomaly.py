"""
Anomaly entity.

The result of a domain rule detecting a problem (see
domain/rules/anomaly_detection.py). `id` is None for a freshly-detected
anomaly that hasn't been persisted yet; the repository populates it on
save/read. `resolved`, `acknowledged_by`, and `blockchain_ref` were
deliberately deferred through M1-M3 as lifecycle/workflow fields owned by
whichever milestone first has a caller for them — that's this one
(Milestone 4's alert-acknowledgement endpoint and blockchain-linking in
IngestTelemetryUseCase).
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
    id: str | None = None
    resolved: bool = False
    acknowledged_by: str | None = None
    blockchain_ref: str | None = None
