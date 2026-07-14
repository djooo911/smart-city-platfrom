"""
Fallback telemetry simulator — Milestone 6.

Plays the same role as the ESP32 firmware (Milestone 5): logs in as the
shared "lamp-device" operator account, generates a plausible sensor
reading, and POSTs it to the live backend's telemetry endpoint. Exists so
a demo doesn't hard-depend on Wokwi being open and reachable (per
docs/architecture.md §11's risk table).

Deliberately a standalone HTTP client, not an internal app.* module: it
talks to the backend exactly like any other client (ESP32 or otherwise),
reusing zero backend internals. The only dependency beyond stdlib is
httpx, already pinned in requirements.txt for FastAPI's TestClient.

Run from `backend/`:
    python simulator/replay.py --device-id lamp-001
    python simulator/replay.py --device-id lamp-001 --device-id lamp-002 --interval 10
    python simulator/replay.py --once   # single reading, then exit (quick demo/test)

Requires DEVICE_USERNAME / DEVICE_PASSWORD (env vars or --username/
--password), matching the backend's DEVICE_SEED_PASSWORD-seeded
"lamp-device" account (see backend/app/infrastructure/mongo/seed.py).
"""

import argparse
import logging
import math
import os
import random
import time
from datetime import datetime, timezone

import httpx

logger = logging.getLogger("replay_simulator")

DEFAULT_BASE_URL = "https://smart-city-platfrom.onrender.com/api/v1"
DEFAULT_INTERVAL_SECONDS = 15
TOKEN_REFRESH_INTERVAL_SECONDS = 45 * 60  # mirrors the ESP32 firmware's proactive refresh
VEHICLE_PROXIMITY_THRESHOLD_CM = 150.0
VEHICLE_DETECTION_PROBABILITY = 0.2
PEDESTRIAN_DETECTION_PROBABILITY = 0.3


def _utc_now_naive() -> datetime:
    # Matches this project's naive-UTC convention (see block.py, lamps.py).
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _synthetic_ambient_light_pct(now: datetime) -> float:
    """
    A smooth day/night curve (peaks at midday, near-zero at midnight) plus
    a little noise, so a demo run shows the energy-optimization night
    discount kicking in realistically rather than pure random noise.
    """
    hour_fraction = (now.hour + now.minute / 60) / 24
    curve = max(0.0, math.sin(hour_fraction * 2 * math.pi - math.pi / 2))
    noise = random.uniform(-5, 5)
    return max(0.0, min(100.0, curve * 100 + noise))


def _synthetic_reading(device_id: str, current_brightness_pct: float) -> dict:
    now = _utc_now_naive()
    pir_triggered = random.random() < PEDESTRIAN_DETECTION_PROBABILITY
    vehicle_detected = random.random() < VEHICLE_DETECTION_PROBABILITY
    distance_cm = (
        random.uniform(20, VEHICLE_PROXIMITY_THRESHOLD_CM - 10)
        if vehicle_detected
        else random.uniform(VEHICLE_PROXIMITY_THRESHOLD_CM + 10, 400)
    )

    return {
        "timestamp": now.isoformat(timespec="seconds"),
        "ambient_light_pct": round(_synthetic_ambient_light_pct(now), 1),
        "pir_triggered": pir_triggered,
        "distance_cm": round(distance_cm, 1),
        "vehicle_detected": vehicle_detected,
        "led_brightness_pct": round(current_brightness_pct, 1),
    }


class SimulatedDevice:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.current_brightness_pct = 50.0


def login(client: httpx.Client, base_url: str, username: str, password: str) -> str:
    response = client.post(f"{base_url}/auth/login", json={"username": username, "password": password})
    response.raise_for_status()
    return response.json()["data"]["access_token"]


def fetch_current_brightness(client: httpx.Client, base_url: str, token: str, device_id: str) -> float | None:
    """
    Best-effort lookup of the lamp's real current brightness, so the first
    telemetry POST reflects reality instead of a hardcoded guess and
    doesn't trip a spurious actuator_mismatch anomaly. Returns None (caller
    keeps the default) if the lamp doesn't exist yet or the request fails.
    """
    try:
        response = client.get(f"{base_url}/lamps/{device_id}", headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        return response.json()["data"]["current_brightness_pct"]
    except httpx.HTTPError:
        return None


def send_telemetry(client: httpx.Client, base_url: str, token: str, device: SimulatedDevice) -> None:
    reading = _synthetic_reading(device.device_id, device.current_brightness_pct)

    response = client.post(
        f"{base_url}/lamps/{device.device_id}/telemetry",
        json=reading,
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code == 401:
        raise PermissionError("token expired or rejected")

    response.raise_for_status()
    body = response.json()["data"]
    device.current_brightness_pct = body["brightness_pct"]

    anomaly_summary = (
        f", {len(body['anomalies'])} anomaly(ies)" if body["anomalies"] else ""
    )
    logger.info(
        "%s: ambient=%.1f%% pir=%s vehicle=%s -> brightness=%.1f%%%s",
        device.device_id,
        reading["ambient_light_pct"],
        reading["pir_triggered"],
        reading["vehicle_detected"],
        body["brightness_pct"],
        anomaly_summary,
    )


def run(base_url: str, username: str, password: str, device_ids: list[str], interval: float, once: bool) -> None:
    devices = [SimulatedDevice(device_id) for device_id in device_ids]

    with httpx.Client(timeout=30.0) as client:
        token = login(client, base_url, username, password)
        logger.info("Logged in as %r", username)
        last_login_time = time.monotonic()

        for device in devices:
            real_brightness = fetch_current_brightness(client, base_url, token, device.device_id)
            if real_brightness is not None:
                device.current_brightness_pct = real_brightness

        while True:
            if time.monotonic() - last_login_time > TOKEN_REFRESH_INTERVAL_SECONDS:
                token = login(client, base_url, username, password)
                last_login_time = time.monotonic()
                logger.info("Re-authenticated")

            for device in devices:
                try:
                    send_telemetry(client, base_url, token, device)
                except PermissionError:
                    token = login(client, base_url, username, password)
                    last_login_time = time.monotonic()
                    send_telemetry(client, base_url, token, device)
                except httpx.HTTPStatusError as exc:
                    logger.warning("%s: telemetry POST failed: %s", device.device_id, exc)

            if once:
                return

            time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--device-id", action="append", dest="device_ids", help="repeatable; defaults to lamp-001")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_SECONDS)
    parser.add_argument("--base-url", default=os.environ.get("SIMULATOR_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--username", default=os.environ.get("DEVICE_USERNAME", "lamp-device"))
    parser.add_argument("--password", default=os.environ.get("DEVICE_PASSWORD"))
    parser.add_argument("--once", action="store_true", help="send a single reading per device, then exit")
    args = parser.parse_args()

    if not args.password:
        parser.error("--password or DEVICE_PASSWORD env var is required")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")

    run(
        base_url=args.base_url,
        username=args.username,
        password=args.password,
        device_ids=args.device_ids or ["lamp-001"],
        interval=args.interval,
        once=args.once,
    )


if __name__ == "__main__":
    main()
