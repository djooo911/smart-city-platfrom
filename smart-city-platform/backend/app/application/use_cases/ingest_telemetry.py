"""
IngestTelemetryUseCase — the HTTP telemetry-ingestion path implied by
docker-compose.yml's ESP32-over-HTTP decision (see main.py's docstring).

Per reading: save it, compute the new target brightness, run the two
anomaly rules that make sense at ingestion time (see module-level note
below on why lamp_offline/traffic_spike are NOT run here), update the
lamp's state, and for each detected anomaly, persist it and append a
blockchain block linking back to it.

Uses `reading.timestamp` (the device's own clock) as the "now" for energy
optimization, anomaly detection, and blockchain mining -- NOT server
wall-clock time. A device's telemetry describes conditions at the moment
it sampled them; using the server's processing time instead would make
the night-window energy discount (and anomaly `detected_at` stamps)
depend on network/processing latency rather than actual conditions.

Anomaly rules NOT run here, deliberately (Milestone 4 scope note):
- detect_lamp_offline: a lamp actively POSTing telemetry is by definition
  not offline. Offline detection belongs in a periodic sweep over lamps
  that HAVEN'T reported recently -- no scheduler exists yet.
- detect_traffic_spike: needs a traffic baseline that doesn't exist yet
  (no TrafficEvent entity / traffic_stats collection -- see M1/M4 scope
  notes).
"""

import dataclasses

from app.application.dto.result import IngestTelemetryResult
from app.application.use_cases._blockchain_helpers import load_or_create_chain
from app.domain.entities.anomaly import Anomaly
from app.domain.entities.enums import LampStatus
from app.domain.entities.lamp_config import LampConfig
from app.domain.entities.lamp_node import LampNode
from app.domain.entities.sensor_reading import SensorReading
from app.domain.interfaces.anomaly_repository import AnomalyRepository
from app.domain.interfaces.blockchain_repository import BlockchainRepository
from app.domain.interfaces.lamp_repository import LampRepository
from app.domain.interfaces.sensor_reading_repository import SensorReadingRepository
from app.domain.rules.anomaly_detection import detect_actuator_mismatch, detect_sensor_out_of_range
from app.domain.rules.energy_optimization import compute_target_brightness


class IngestTelemetryUseCase:
    def __init__(
        self,
        sensor_reading_repository: SensorReadingRepository,
        lamp_repository: LampRepository,
        anomaly_repository: AnomalyRepository,
        blockchain_repository: BlockchainRepository,
    ):
        self._sensor_reading_repository = sensor_reading_repository
        self._lamp_repository = lamp_repository
        self._anomaly_repository = anomaly_repository
        self._blockchain_repository = blockchain_repository

    async def execute(self, reading: SensorReading) -> IngestTelemetryResult:
        now = reading.timestamp

        await self._sensor_reading_repository.save(reading)

        existing_lamp = await self._lamp_repository.get(reading.device_id)
        config = existing_lamp.config if existing_lamp else LampConfig()

        target_brightness = compute_target_brightness(reading, config, now)

        detected: list[Anomaly] = []

        range_anomaly = detect_sensor_out_of_range(reading, now)
        if range_anomaly:
            detected.append(range_anomaly)

        if existing_lamp is not None:
            mismatch_anomaly = detect_actuator_mismatch(
                reading, existing_lamp.current_brightness_pct, config, now
            )
            if mismatch_anomaly:
                detected.append(mismatch_anomaly)

        await self._lamp_repository.upsert(
            LampNode(
                device_id=reading.device_id,
                status=LampStatus.ONLINE,
                current_brightness_pct=target_brightness,
                last_seen=reading.timestamp,
                config=config,
                location=existing_lamp.location if existing_lamp else None,
            )
        )

        persisted_anomalies: list[Anomaly] = []
        for anomaly in detected:
            anomaly_id = await self._anomaly_repository.save(anomaly)

            chain = await load_or_create_chain(self._blockchain_repository, now)
            block = chain.add_block(
                {
                    "event_type": "anomaly_detected",
                    "device_id": anomaly.device_id,
                    "anomaly_type": anomaly.type.value,
                },
                now,
            )
            await self._blockchain_repository.append_block(block)
            await self._anomaly_repository.set_blockchain_ref(anomaly_id, block.hash)

            persisted_anomalies.append(
                dataclasses.replace(anomaly, id=anomaly_id, blockchain_ref=block.hash)
            )

        return IngestTelemetryResult(brightness_pct=target_brightness, anomalies=persisted_anomalies)
