# Smart City Public Lighting and Traffic Monitoring with Blockchain Traceability

University engineering project. A Smart City platform that simulates
intelligent street lighting and traffic monitoring, records anomalies and
infrastructure decisions on a local (non-cryptocurrency) blockchain for
auditability, and exposes both a REST API and a web dashboard.

> **Status:** Milestone 0 — project scaffold only. No business logic,
> blockchain, sensor processing, or dashboard UI has been implemented yet.
> See `docs/architecture.md` for the full design.

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
├── backend/          FastAPI application (Clean Architecture layers)
├── frontend/          Static HTML/CSS/JS dashboard (placeholder for now)
├── iot-firmware/      ESP32 firmware for Wokwi simulation (placeholder for now)
├── docs/              Architecture documentation and diagrams
└── docker-compose.yml Local orchestration: backend + mongo + frontend
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

## Project Milestones

See `docs/architecture.md` §9 for the full milestone plan. Current status:

- [x] **M0** — Project scaffold, Docker Compose, health check
- [ ] **M1** — Domain & application core (energy optimization, anomaly rules)
- [ ] **M2** — Blockchain engine
- [ ] **M3** — MongoDB repositories & collections
- [ ] **M4** — REST API layer (lamps, traffic, alerts, blockchain explorer)
- [ ] **M5** — IoT simulation (Wokwi) + HTTP telemetry ingestion
- [ ] **M6** — Fallback Python telemetry simulator
- [ ] **M7** — Web dashboard (Leaflet map, charts, blockchain explorer UI)
- [ ] **M8** — Regression testing & CI
- [ ] **M9** — Hardening & documentation

## License / Academic Context

Developed as a university engineering project. Not intended for production
deployment as-is.
