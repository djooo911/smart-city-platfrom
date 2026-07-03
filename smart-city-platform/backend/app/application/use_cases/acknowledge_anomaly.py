"""
AcknowledgeAnomalyUseCase — operator+ marks an alert as reviewed.
"""

import dataclasses

from app.domain.entities.anomaly import Anomaly
from app.domain.interfaces.anomaly_repository import AnomalyRepository


class AcknowledgeAnomalyUseCase:
    def __init__(self, anomaly_repository: AnomalyRepository):
        self._anomaly_repository = anomaly_repository

    async def execute(self, anomaly_id: str, acknowledged_by: str) -> Anomaly:
        anomaly = await self._anomaly_repository.get_by_id(anomaly_id)
        if anomaly is None:
            raise ValueError(f"Unknown anomaly: {anomaly_id}")

        await self._anomaly_repository.mark_acknowledged(anomaly_id, acknowledged_by)
        return dataclasses.replace(anomaly, resolved=True, acknowledged_by=acknowledged_by)
