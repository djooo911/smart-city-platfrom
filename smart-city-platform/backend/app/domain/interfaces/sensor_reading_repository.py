"""
SensorReadingRepository — persistence contract for SensorReading.
"""

from typing import Protocol

from app.domain.entities.sensor_reading import SensorReading


class SensorReadingRepository(Protocol):
    async def save(self, reading: SensorReading) -> None: ...

    async def get_latest(self, device_id: str) -> SensorReading | None: ...
