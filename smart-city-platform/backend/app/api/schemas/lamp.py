"""
Request bodies for the lamps router. Response shapes stay plain dicts
(see routers/lamps.py's serialization helpers) -- no response schemas
here, consistent with the rest of the API.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryIngestRequest(BaseModel):
    timestamp: datetime
    ambient_light_pct: float
    pir_triggered: bool
    distance_cm: float | None = None
    vehicle_detected: bool
    led_brightness_pct: float


class LampOverrideRequest(BaseModel):
    brightness_pct: float = Field(ge=0, le=100)
    reason: str


class LampConfigUpdateRequest(BaseModel):
    min_brightness_pct: float = Field(ge=0, le=100)
    max_brightness_pct: float = Field(ge=0, le=100)
    offline_timeout_seconds: int = Field(gt=0)
    actuator_mismatch_tolerance_pct: float = Field(ge=0, le=100)
