# Demo Script

A ~10-minute guided walkthrough of the running system, for a live
presentation or self-check before submission. Assumes the deployed Render
backend (`https://smart-city-platfrom.onrender.com`) and a live database
seeded via `python -m app.infrastructure.mongo.seed` (see README).

Render's free tier spins down after inactivity — hit the health check
first and give it ~30s if it's cold:
```
curl https://smart-city-platfrom.onrender.com/api/v1/system/health
```

## 1. Start the dashboard

```bash
python -m http.server 8081 --directory frontend
```
Open `http://localhost:8081`. `frontend/js/api.js` already points at the
live Render backend.

## 2. Log in and show role-gating

Log in as `admin` (or `regression-viewer` from `tests/regression/conftest.py`
if a lower-privilege account is more illustrative). Point out:
- No anonymous read access anywhere except `/auth/login` and
  `/system/health` — every other endpoint requires at least `viewer`.
- The override/config forms on the Lamps tab only appear for
  `operator`/`admin` roles (client-side UX only; the backend enforces the
  real check regardless — try the same request as a viewer via `/docs` to
  show the 403).

## 3. Map tab

Three markers around Tunis (Avenue Habib Bourguiba, Rue de Marseille,
Avenue Mohamed V), colored by status (green = online, red = offline).
Click one to show the popup with live status/brightness/last-seen.

## 4. Live telemetry — Wokwi or the fallback simulator

Either works; the dashboard doesn't know or care which sent the data.

**Wokwi:** open the `iot-firmware` project, start the simulation, and
narrate the serial console (`WiFi connected`, `Login successful`,
`Telemetry OK ... -> brightness=NN.N%`). Move the potentiometer (ambient
light) and PIR toggle in Wokwi's UI and point out the brightness reacting
within ~15s on the dashboard (polling interval).

**Fallback simulator** (no Wokwi needed):
```bash
cd backend
python simulator/replay.py --device-id lamp-001 --interval 10 --password <DEVICE_SEED_PASSWORD>
```
Same effect — logs in as `lamp-device`, generates a day/night ambient-light
curve plus randomized PIR/vehicle events, posts to the same
`/lamps/{id}/telemetry` endpoint a real device would use.

## 5. Lamps tab — history chart + manual override

Click a lamp: the brightness/ambient-light history chart renders from
`GET /lamps/{id}/history` (populated by whichever of step 4 you ran). As
`operator`+, submit the override form — a manual brightness override with
a reason, which also creates a blockchain-logged configuration-change
event (see step 7).

## 6. Trigger and acknowledge an anomaly

Easiest reliable trigger: an **actuator mismatch** (reported LED
brightness differs from the lamp's last known brightness by more than its
`actuator_mismatch_tolerance_pct`, default 15%). Via `/docs` → POST
`/api/v1/lamps/lamp-001/telemetry` (as `lamp-device` or any operator+):
```json
{
  "timestamp": "2026-07-14T12:00:00",
  "ambient_light_pct": 50,
  "pir_triggered": false,
  "vehicle_detected": false,
  "led_brightness_pct": 5
}
```
If `lamp-001`'s current brightness is well above 5%, this trips
`actuator_mismatch`. Switch to the Alerts tab — the anomaly appears; as
`operator`+, click "Acquitter" to acknowledge it and show the state flip.

## 7. Blockchain tab

List blocks (each anomaly and configuration change from steps 5–6 minted
one), click a block for the raw JSON detail (index, timestamp, data,
previous_hash, nonce, hash), then click "Verify Chain" — confirms the
SHA-256 hash-chain is intact end to end. Worth narrating in plain terms:
this isn't a cryptocurrency, it's a tamper-evident append-only log —
editing any historical block's data changes its hash, which breaks every
subsequent block's `previous_hash` link, which `verify_chain()` catches.

## 8. Wrap-up: CI

Point at the green check on the GitHub repo (or the Actions tab) — every
push runs the full `unit` + `integration` + `regression` pytest suite
against a real MongoDB service container, not mocks.
