"""
Regression test for the /system/health endpoint.

This is the first entry in what will become the full API regression suite
(per the DevOps requirement in the project brief). Its purpose right now
is narrow: prove that the FastAPI app boots, the MongoDB connection
lifecycle works, and the endpoint returns the expected response envelope
shape (`{"data": ..., "meta": ...}`) that every future endpoint will
follow.
"""

import pytest

pytestmark = pytest.mark.regression


def test_health_check_returns_ok_status(client):
    response = client.get("/api/v1/system/health")

    assert response.status_code == 200

    body = response.json()
    assert "data" in body
    assert "meta" in body
    assert body["data"]["status"] in {"ok", "degraded"}
    assert "mongodb" in body["data"]["dependencies"]
