"""
Alerts: list anomalies with optional filters (viewer+), acknowledge one
(operator+).
"""

from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_acknowledge_anomaly_use_case, get_anomaly_repository
from app.api.serializers import serialize_anomaly
from app.application.use_cases.acknowledge_anomaly import AcknowledgeAnomalyUseCase
from app.domain.entities.enums import AnomalySeverity, Role
from app.domain.interfaces.anomaly_repository import AnomalyRepository
from app.security.rbac import CurrentUser, require_role

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(
    device_id: str | None = Query(default=None),
    resolved: bool | None = Query(default=None),
    severity: AnomalySeverity | None = Query(default=None),
    anomaly_repository: AnomalyRepository = Depends(get_anomaly_repository),
    _current_user: CurrentUser = Depends(require_role(Role.VIEWER)),
) -> dict:
    anomalies = await anomaly_repository.list_all(
        device_id=device_id, resolved=resolved, severity=severity
    )
    return {"data": [serialize_anomaly(anomaly) for anomaly in anomalies], "meta": {}}


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    use_case: AcknowledgeAnomalyUseCase = Depends(get_acknowledge_anomaly_use_case),
    current_user: CurrentUser = Depends(require_role(Role.OPERATOR)),
) -> dict:
    try:
        anomaly = await use_case.execute(alert_id, current_user.username)
    except (ValueError, InvalidId):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    return {"data": serialize_anomaly(anomaly), "meta": {}}
