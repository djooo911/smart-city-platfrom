"""
Lamps: list/detail/history (viewer+), telemetry ingestion (operator+ --
the HTTP path implied by docker-compose.yml's ESP32-over-HTTP decision,
not literally in architecture.md §5.1, which assumed MQTT), manual
override (operator+), and threshold config updates (admin).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import (
    get_ingest_telemetry_use_case,
    get_lamp_repository,
    get_override_lighting_use_case,
    get_sensor_reading_repository,
    get_update_lamp_config_use_case,
)
from app.api.schemas.lamp import (
    LampConfigUpdateRequest,
    LampOverrideRequest,
    TelemetryIngestRequest,
)
from app.api.serializers import serialize_anomaly, serialize_lamp, serialize_reading
from app.application.use_cases.ingest_telemetry import IngestTelemetryUseCase
from app.application.use_cases.override_lighting import OverrideLightingUseCase
from app.application.use_cases.update_lamp_config import UpdateLampConfigUseCase
from app.domain.entities.enums import Role
from app.domain.entities.lamp_config import LampConfig
from app.domain.entities.sensor_reading import SensorReading
from app.domain.interfaces.lamp_repository import LampRepository
from app.domain.interfaces.sensor_reading_repository import SensorReadingRepository
from app.security.rbac import CurrentUser, require_role

router = APIRouter(prefix="/lamps", tags=["lamps"])


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.get("")
async def list_lamps(
    lamp_repository: LampRepository = Depends(get_lamp_repository),
    _current_user: CurrentUser = Depends(require_role(Role.VIEWER)),
) -> dict:
    lamps = await lamp_repository.list_all()
    return {"data": [serialize_lamp(lamp) for lamp in lamps], "meta": {}}


@router.get("/{device_id}")
async def get_lamp(
    device_id: str,
    lamp_repository: LampRepository = Depends(get_lamp_repository),
    _current_user: CurrentUser = Depends(require_role(Role.VIEWER)),
) -> dict:
    lamp = await lamp_repository.get(device_id)
    if lamp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lamp not found")

    return {"data": serialize_lamp(lamp), "meta": {}}


@router.get("/{device_id}/history")
async def get_lamp_history(
    device_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sensor_reading_repository: SensorReadingRepository = Depends(get_sensor_reading_repository),
    _current_user: CurrentUser = Depends(require_role(Role.VIEWER)),
) -> dict:
    readings = await sensor_reading_repository.list_history(device_id, page, page_size)
    return {
        "data": [serialize_reading(reading) for reading in readings],
        "meta": {"page": page, "page_size": page_size},
    }


@router.post("/{device_id}/telemetry", status_code=status.HTTP_201_CREATED)
async def ingest_telemetry(
    device_id: str,
    body: TelemetryIngestRequest,
    use_case: IngestTelemetryUseCase = Depends(get_ingest_telemetry_use_case),
    _current_user: CurrentUser = Depends(require_role(Role.OPERATOR)),
) -> dict:
    reading = SensorReading(
        device_id=device_id,
        timestamp=body.timestamp,
        ambient_light_pct=body.ambient_light_pct,
        pir_triggered=body.pir_triggered,
        distance_cm=body.distance_cm,
        vehicle_detected=body.vehicle_detected,
        led_brightness_pct=body.led_brightness_pct,
    )
    result = await use_case.execute(reading)

    return {
        "data": {
            "brightness_pct": result.brightness_pct,
            "anomalies": [serialize_anomaly(anomaly) for anomaly in result.anomalies],
        },
        "meta": {},
    }


@router.post("/{device_id}/override")
async def override_lamp(
    device_id: str,
    body: LampOverrideRequest,
    use_case: OverrideLightingUseCase = Depends(get_override_lighting_use_case),
    current_user: CurrentUser = Depends(require_role(Role.OPERATOR)),
) -> dict:
    try:
        lamp = await use_case.execute(
            device_id, body.brightness_pct, current_user.username, body.reason, _utc_now()
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lamp not found")

    return {"data": serialize_lamp(lamp), "meta": {}}


@router.patch("/{device_id}/config")
async def update_lamp_config(
    device_id: str,
    body: LampConfigUpdateRequest,
    use_case: UpdateLampConfigUseCase = Depends(get_update_lamp_config_use_case),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN)),
) -> dict:
    config = LampConfig(**body.model_dump())
    try:
        lamp = await use_case.execute(device_id, config, current_user.username, _utc_now())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lamp not found")

    return {"data": serialize_lamp(lamp), "meta": {}}
