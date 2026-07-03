"""
AnomalyRepository — persistence contract for Anomaly.

Lifecycle-transition methods (mark_acknowledged, set_blockchain_ref) and
general-purpose querying (list_all, get_by_id) arrive in Milestone 4,
exactly when their callers do: the alert-acknowledgement endpoint and
IngestTelemetryUseCase's anomaly-to-block linking. M3 deliberately left
this Protocol narrower than this.
"""

from typing import Protocol

from app.domain.entities.anomaly import Anomaly
from app.domain.entities.enums import AnomalySeverity


class AnomalyRepository(Protocol):
    async def save(self, anomaly: Anomaly) -> str: ...

    async def list_by_device(self, device_id: str) -> list[Anomaly]: ...

    async def list_all(
        self,
        device_id: str | None = None,
        resolved: bool | None = None,
        severity: AnomalySeverity | None = None,
    ) -> list[Anomaly]: ...

    async def get_by_id(self, anomaly_id: str) -> Anomaly | None: ...

    async def mark_acknowledged(self, anomaly_id: str, acknowledged_by: str) -> None: ...

    async def set_blockchain_ref(self, anomaly_id: str, block_hash: str) -> None: ...
