"""
AnomalyRepository — persistence contract for Anomaly.

Deliberately does not expose lifecycle-transition methods (e.g.
mark_resolved, acknowledge) in Milestone 3: no use case needs them yet
(that arrives with Milestone 4's alert-acknowledgement endpoint). Adding
them now would grow this Protocol ahead of any caller.
"""

from typing import Protocol

from app.domain.entities.anomaly import Anomaly


class AnomalyRepository(Protocol):
    async def save(self, anomaly: Anomaly) -> None: ...

    async def list_by_device(self, device_id: str) -> list[Anomaly]: ...
