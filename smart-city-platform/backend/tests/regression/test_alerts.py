"""
Regression tests for the /alerts endpoints.
"""

import uuid

import pytest
from tests.regression.conftest import auth_headers

from app.domain.entities.enums import Role

pytestmark = pytest.mark.regression


def _device_id() -> str:
    return f"lamp-regression-{uuid.uuid4().hex[:8]}"


def _trigger_anomaly(client, device_id: str) -> dict:
    response = client.post(
        f"/api/v1/lamps/{device_id}/telemetry",
        json={
            "timestamp": "2026-07-03T10:00:00",
            "ambient_light_pct": -5.0,
            "pir_triggered": False,
            "distance_cm": 100.0,
            "vehicle_detected": False,
            "led_brightness_pct": 50.0,
        },
        headers=auth_headers(client, Role.OPERATOR),
    )
    return response.json()["data"]["anomalies"][0]


def test_list_alerts_requires_auth(client):
    response = client.get("/api/v1/alerts")

    assert response.status_code == 401


def test_list_alerts_filters_by_device_id(client):
    device_id = _device_id()
    anomaly = _trigger_anomaly(client, device_id)

    response = client.get(
        f"/api/v1/alerts?device_id={device_id}", headers=auth_headers(client, Role.VIEWER)
    )

    assert response.status_code == 200
    alerts = response.json()["data"]
    assert len(alerts) == 1
    assert alerts[0]["id"] == anomaly["id"]
    assert alerts[0]["resolved"] is False


def test_acknowledge_requires_operator_role(client):
    device_id = _device_id()
    anomaly = _trigger_anomaly(client, device_id)

    response = client.post(
        f"/api/v1/alerts/{anomaly['id']}/acknowledge",
        headers=auth_headers(client, Role.VIEWER),
    )

    assert response.status_code == 403


def test_acknowledge_marks_alert_resolved(client):
    device_id = _device_id()
    anomaly = _trigger_anomaly(client, device_id)

    response = client.post(
        f"/api/v1/alerts/{anomaly['id']}/acknowledge",
        headers=auth_headers(client, Role.OPERATOR),
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["resolved"] is True
    assert body["acknowledged_by"] == "regression-operator"


def test_acknowledge_unknown_alert_returns_404(client):
    response = client.post(
        "/api/v1/alerts/000000000000000000000000/acknowledge",
        headers=auth_headers(client, Role.OPERATOR),
    )

    assert response.status_code == 404


def test_acknowledge_malformed_alert_id_returns_404(client):
    response = client.post(
        "/api/v1/alerts/not-a-valid-object-id/acknowledge",
        headers=auth_headers(client, Role.OPERATOR),
    )

    assert response.status_code == 404
