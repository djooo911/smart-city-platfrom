"""
LampNode entity.

Represents the current known state of one lamp node (device registry +
live status), mirroring `lamp_nodes` in docs/architecture.md §6.2.

Deliberately has no mutation methods: deciding *when* a lamp transitions
between online/offline or gets a new brightness applied is an application
use-case concern (Milestone 3+, once a repository exists to persist the
transition), not something the entity should decide on its own.
"""

from dataclasses import dataclass
from datetime import datetime

from app.domain.entities.enums import LampStatus
from app.domain.entities.lamp_config import LampConfig
from app.domain.entities.location import Location


@dataclass
class LampNode:
    device_id: str
    status: LampStatus
    current_brightness_pct: float
    last_seen: datetime
    config: LampConfig
    location: Location | None = None
