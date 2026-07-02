"""
Energy optimization rule.

Computes the target LED brightness for a lamp node from its latest sensor
reading. Pure function, framework-agnostic: no Mongo, no HTTP, no clock
access (the caller supplies `now`) so it stays deterministic and trivially
unit-testable.

Algorithm:
1. Defensively clamp `ambient_light_pct` to [0, 100] — out-of-range values
   are an anomaly-detection concern, not something this rule should choke
   on or amplify.
2. `base = 100 - ambient_light_pct`: darker ambient conditions need more
   artificial light.
3. Presence (PIR motion or a detected vehicle) always wins: brightness is
   at least 90%, regardless of time of day. Safety takes priority over
   energy savings whenever someone might be nearby.
4. Otherwise (idle, nobody around), the lamp dims to save energy: half of
   `base`, with an extra 30% cut during the 00:00-05:00 low-traffic window.
5. The result is clamped to the node's configured [min, max] brightness
   bounds.
"""

from datetime import datetime, time

from app.domain.entities.lamp_config import LampConfig
from app.domain.entities.sensor_reading import SensorReading

_NIGHT_WINDOW_START = time(0, 0)
_NIGHT_WINDOW_END = time(5, 0)

_PRESENCE_BRIGHTNESS_PCT = 90.0
_IDLE_BRIGHTNESS_FACTOR = 0.5
_NIGHT_IDLE_FACTOR = 0.7


def _is_night_window(now: datetime) -> bool:
    return _NIGHT_WINDOW_START <= now.time() < _NIGHT_WINDOW_END


def compute_target_brightness(
    reading: SensorReading, config: LampConfig, now: datetime
) -> float:
    ambient_light_pct = max(0.0, min(100.0, reading.ambient_light_pct))
    base = 100.0 - ambient_light_pct

    if reading.pir_triggered or reading.vehicle_detected:
        brightness = max(base, _PRESENCE_BRIGHTNESS_PCT)
    else:
        brightness = base * _IDLE_BRIGHTNESS_FACTOR
        if _is_night_window(now):
            brightness *= _NIGHT_IDLE_FACTOR

    return max(config.min_brightness_pct, min(config.max_brightness_pct, brightness))
