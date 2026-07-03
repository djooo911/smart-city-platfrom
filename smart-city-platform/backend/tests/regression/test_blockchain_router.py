"""
Regression tests for the /blockchain explorer endpoints.
"""

import uuid

import pytest
from tests.regression.conftest import auth_headers

from app.domain.entities.enums import Role

pytestmark = pytest.mark.regression


def _device_id() -> str:
    return f"lamp-regression-{uuid.uuid4().hex[:8]}"


def test_blockchain_endpoints_require_auth(client):
    assert client.get("/api/v1/blockchain/blocks").status_code == 401
    assert client.get("/api/v1/blockchain/verify").status_code == 401


def test_verify_chain_reports_valid(client):
    response = client.get(
        "/api/v1/blockchain/verify", headers=auth_headers(client, Role.VIEWER)
    )

    assert response.status_code == 200
    assert response.json()["data"]["valid"] is True


def test_list_blocks_is_paginated(client):
    response = client.get(
        "/api/v1/blockchain/blocks?page=1&page_size=1", headers=auth_headers(client, Role.VIEWER)
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) <= 1
    assert body["meta"]["page"] == 1
    assert body["meta"]["page_size"] == 1


def test_get_block_zero_returns_first_block(client):
    response = client.get(
        "/api/v1/blockchain/blocks/0", headers=auth_headers(client, Role.VIEWER)
    )

    assert response.status_code == 200
    assert response.json()["data"]["index"] == 0


def test_get_unknown_block_index_returns_404(client):
    response = client.get(
        "/api/v1/blockchain/blocks/999999", headers=auth_headers(client, Role.VIEWER)
    )

    assert response.status_code == 404


def test_events_by_device_only_returns_matching_blocks(client):
    device_id = _device_id()
    client.post(
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

    response = client.get(
        f"/api/v1/blockchain/events?device_id={device_id}",
        headers=auth_headers(client, Role.VIEWER),
    )

    assert response.status_code == 200
    events = response.json()["data"]
    assert len(events) == 1
    assert events[0]["data"]["device_id"] == device_id
