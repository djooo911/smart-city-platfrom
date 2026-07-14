# Smart City Public Lighting and Traffic Monitoring with Blockchain Traceability

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![CI](https://github.com/djooo911/smart-city-platfrom/actions/workflows/ci.yml/badge.svg)](https://github.com/djooo911/smart-city-platfrom/actions/workflows/ci.yml)

University engineering project. A Smart City platform that simulates
intelligent street lighting and traffic monitoring, records anomalies and
infrastructure decisions on a local (non-cryptocurrency) blockchain for
auditability, and exposes both a REST API and a web dashboard.

> **Status:** All 9 milestones complete (see below). Live backend deployed
> on Render, ESP32 firmware simulated in Wokwi, web dashboard and fallback
> Python simulator both included. See `docs/architecture.md` for the full
> design and [`docs/demo-script.md`](docs/demo-script.md) for a guided
> walkthrough.

## Architecture at a Glance

- **IoT simulation (Wokwi):** ESP32 + potentiometer (LDR proxy) + PIR +
  HC-SR04 + PWM LED. Sends telemetry to the backend over **HTTP REST**.
- **Backend:** Python + FastAPI, Clean-Architecture-inspired layering
  (domain / application / infrastructure / api).
- **Database:** MongoDB.
- **Blockchain:** custom local Python blockchain (not a cryptocurrency) —
  used only for tamper-evident logging of anomalies and configuration
  changes.
- **Frontend:** HTML + CSS + JavaScript, with Leaflet.js for the city map.
- **DevOps:** Docker, Docker Compose, Pytest for API regression testing.

Full details, diagrams, API design, MongoDB schemas, and blockchain
structure: see [`docs/architecture.md`](docs/architecture.md).

## Project Structure

```
smart-city-platform/
├── backend/           FastAPI application (Clean Architecture layers),
│                      pytest suite, and the M6 fallback telemetry simulator
│                      (backend/simulator/replay.py)
├── frontend/          Static HTML/CSS/JS dashboard (Leaflet map, charts,
│                      blockchain explorer — no build step, native ES modules)
├── iot-firmware/      ESP32 firmware (Wokwi simulation): LDR, PIR, HC-SR04,
│                      PWM LED, HTTP REST telemetry client
├── docs/              Architecture documentation and the demo script
└── docker-compose.yml Local orchestration: backend + mongo + frontend

../.github/workflows/ci.yml   M8 CI pipeline (one level above this
                               directory, at the actual git repo root)
```

## Prerequisites

- Docker and Docker Compose installed.
- (Optional, for local non-Docker development) Python 3.12+.
- A Wokwi account/project for the IoT simulation layer (added in a later
  milestone).

## Running the Project

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Build and start the stack:
   ```bash
   docker-compose up --build
   ```
3. Once running:
   - Backend API: http://localhost:8000
   - Interactive API docs (Swagger UI): http://localhost:8000/docs
   - Health check: http://localhost:8000/api/v1/system/health
   - Frontend (placeholder page): http://localhost:8080
   - MongoDB: exposed on `localhost:27017` (for inspection with e.g. MongoDB Compass)

4. Stop the stack:
   ```bash
   docker-compose down
   ```
   Add `-v` to also remove the MongoDB data volume (full reset).

## Deploying the Backend on Render

The repo includes a [`render.yaml`](render.yaml) Blueprint that deploys the
backend as a Docker web service. Render has no managed MongoDB offering, so
you need a free external cluster (e.g. [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)).

1. Create a free MongoDB Atlas cluster, add a database user, and allow
   network access from anywhere (`0.0.0.0/0`) — simplest option for an
   academic project. Copy the connection string.
2. On [Render](https://dashboard.render.com), click **New > Blueprint** and
   select this GitHub repo. Render will detect `render.yaml` and propose the
   `smart-city-backend` service.
3. Before (or right after) the first deploy, open the service's
   **Environment** tab and set `MONGO_URI` to your Atlas connection string
   (it's intentionally left unset in `render.yaml`).
4. Deploy. Once live, check `https://<your-service>.onrender.com/api/v1/system/health`
   — it should report `"status": "ok"` with `"mongodb": "ok"`.

Note: the free Render plan spins the service down after inactivity, so the
first request after idling can take ~30s to respond.

## Running Tests Locally (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
```

Note: the health check test requires a reachable MongoDB instance (e.g.
`docker-compose up mongo -d` first), since it exercises the real startup
lifecycle rather than mocking the database.

Tests are split into three pytest markers (see `backend/pytest.ini`):
`unit` (no infra), `integration` (real MongoDB, repository layer only),
`regression` (full API via `TestClient`). Run one kind with
`pytest -m unit`, `pytest -m integration`, or `pytest -m regression`.
Both `integration` and `regression` refuse to run against a database
named `smart_city_db` (Render's production name) as a safety guard — copy
`backend/.env.example` to `backend/.env` and use a different
`MONGO_DB_NAME`.

## Running the Fallback Telemetry Simulator (M6)

If Wokwi isn't open/reachable, `backend/simulator/replay.py` generates
plausible sensor readings and posts them to a running backend, exactly
like the ESP32 firmware would:

```bash
cd backend
python simulator/replay.py --device-id lamp-001 --password <DEVICE_SEED_PASSWORD>
python simulator/replay.py --once --password <DEVICE_SEED_PASSWORD>   # single reading, then exit
```

Defaults to the live Render backend and the `lamp-device` account; pass
`--base-url` to point at a local backend instead. See the script's
docstring for the full option list.

## Running the Web Dashboard Locally (M7)

The frontend is static HTML/CSS/JS with no build step — either run it via
`docker-compose up` (serves on `http://localhost:8080`) or directly:

```bash
python -m http.server 8081 --directory frontend
```

Then open `http://localhost:8081`. By default `frontend/js/api.js` points
at the live Render backend, so you can log in and see real data without
running the backend locally — edit `API_BASE_URL` in that file to point
at `http://localhost:8000/api/v1` instead if you're also running the
backend locally.

## Project Milestones

See `docs/architecture.md` §9 for the full milestone plan. Current status:

- [x] **M0** — Project scaffold, Docker Compose, health check
- [x] **M1** — Domain & application core (energy optimization, anomaly rules)
- [x] **M2** — Blockchain engine
- [x] **M3** — MongoDB repositories & collections
- [x] **M4** — REST API layer (lamps, alerts, blockchain explorer, auth/RBAC — traffic + energy-savings endpoints deferred, no data pipeline yet)
- [x] **M5** — IoT simulation (Wokwi) + HTTP telemetry ingestion
- [x] **M6** — Fallback Python telemetry simulator
- [x] **M7** — Web dashboard (Leaflet map, charts, blockchain explorer UI)
- [x] **M8** — Regression testing & CI
- [x] **M9** — Hardening & documentation (README/architecture doc finalized, demo script added)

## License / Academic Context

Developed as a university engineering project. Not intended for production
deployment as-is. Released under the [MIT License](../LICENSE).
