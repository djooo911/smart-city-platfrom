"""
Regression tests for the /lamps endpoints, including telemetry ingestion
triggering an anomaly + blockchain block end-to-end.
"""

import uuid

import pytest
from tests.regression.conftest import auth_headers

from app.domain.entities.enums import Role

pytestmark = pytest.mark.regression


def _device_id() -> str:
    return f"lamp-regression-{uuid.uuid4().hex[:8]}"


def _telemetry_body(**overrides) -> dict:
    defaults = dict(
        timestamp="2026-07-03T10:00:00",
        ambient_light_pct=40.0,
        pir_triggered=False,
        distance_cm=100.0,
        vehicle_detected=False,
        led_brightness_pct=50.0,
    )
    defaults.update(overrides)
    return defaults


def test_list_lamps_requires_auth(client):
    response = client.get("/api/v1/lamps")

    assert response.status_code == 401


def test_list_lamps_with_viewer_token_succeeds(client):
    response = client.get("/api/v1/lamps", headers=auth_headers(client, Role.VIEWER))

    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)


def test_ingest_telemetry_requires_operator_role(client):
    device_id = _device_id()

    response = client.post(
        f"/api/v1/lamps/{device_id}/telemetry",
        json=_telemetry_body(),
        headers=auth_headers(client, Role.VIEWER),
    )

    assert response.status_code == 403


def test_ingest_telemetry_creates_lamp_and_returns_brightness(client):
    device_id = _device_id()

    response = client.post(
        f"/api/v1/lamps/{device_id}/telemetry",
        json=_telemetry_body(ambient_light_pct=40.0),
        headers=auth_headers(client, Role.OPERATOR),
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["brightness_pct"] == 30.0  # base=60, idle -> 60*0.5
    assert body["anomalies"] == []

    lamp_response = client.get(
        f"/api/v1/lamps/{device_id}", headers=auth_headers(client, Role.VIEWER)
    )
    assert lamp_response.status_code == 200
    assert lamp_response.json()["data"]["device_id"] == device_id


def test_ingest_telemetry_with_out_of_range_reading_creates_anomaly_and_block(client):
    device_id = _device_id()

    response = client.post(
        f"/api/v1/lamps/{device_id}/telemetry",
        json=_telemetry_body(ambient_light_pct=-5.0),
        headers=auth_headers(client, Role.OPERATOR),
    )

    assert response.status_code == 201
    anomalies = response.json()["data"]["anomalies"]
    assert len(anomalies) == 1
    assert anomalies[0]["type"] == "sensor_out_of_range"
    assert anomalies[0]["blockchain_ref"] is not None

    events_response = client.get(
        f"/api/v1/blockchain/events?device_id={device_id}",
        headers=auth_headers(client, Role.VIEWER),
    )
    assert events_response.status_code == 200
    events = events_response.json()["data"]
    assert any(event["hash"] == anomalies[0]["blockchain_ref"] for event in events)


def test_get_lamp_history_after_ingestion(client):
    device_id = _device_id()
    client.post(
        f"/api/v1/lamps/{device_id}/telemetry",
        json=_telemetry_body(),
        headers=auth_headers(client, Role.OPERATOR),
    )

    response = client.get(
        f"/api/v1/lamps/{device_id}/history", headers=auth_headers(client, Role.VIEWER)
    )

    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


def test_override_requires_operator_role(client):
    device_id = _device_id()
    client.post(
        f"/api/v1/lamps/{device_id}/telemetry",
        json=_telemetry_body(),
        headers=auth_headers(client, Role.OPERATOR),
    )

    response = client.post(
        f"/api/v1/lamps/{device_id}/override",
        json={"brightness_pct": 80.0, "reason": "manual test"},
        headers=auth_headers(client, Role.VIEWER),
    )

    assert response.status_code == 403


def test_override_applies_brightness_and_returns_404_for_unknown_lamp(client):
    device_id = _device_id()
    client.post(
        f"/api/v1/lamps/{device_id}/telemetry",
        json=_telemetry_body(),
        headers=auth_headers(client, Role.OPERATOR),
    )

    response = client.post(
        f"/api/v1/lamps/{device_id}/override",
        json={"brightness_pct": 80.0, "reason": "manual test"},
        headers=auth_headers(client, Role.OPERATOR),
    )
    assert response.status_code == 200
    assert response.json()["data"]["current_brightness_pct"] == 80.0

    missing_response = client.post(
        f"/api/v1/lamps/{_device_id()}/override",
        json={"brightness_pct": 80.0, "reason": "manual test"},
        headers=auth_headers(client, Role.OPERATOR),
    )
    assert missing_response.status_code == 404


def test_config_update_requires_admin_role(client):
    device_id = _device_id()
    client.post(
        f"/api/v1/lamps/{device_id}/telemetry",
        json=_telemetry_body(),
        headers=auth_headers(client, Role.OPERATOR),
    )

    config_body = {
        "min_brightness_pct": 5.0,
        "max_brightness_pct": 90.0,
        "offline_timeout_seconds": 120,
        "actuator_mismatch_tolerance_pct": 25.0,
    }

    operator_response = client.patch(
        f"/api/v1/lamps/{device_id}/config",
        json=config_body,
        headers=auth_headers(client, Role.OPERATOR),
    )
    assert operator_response.status_code == 403

    admin_response = client.patch(
        f"/api/v1/lamps/{device_id}/config",
        json=config_body,
        headers=auth_headers(client, Role.ADMIN),
    )
    assert admin_response.status_code == 200
    assert admin_response.json()["data"]["config"]["max_brightness_pct"] == 90.0
