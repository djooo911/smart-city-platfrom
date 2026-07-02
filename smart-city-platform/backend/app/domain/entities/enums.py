"""
Shared enums for domain entities.

Kept in their own module (rather than inline in each entity file) so that
`lamp_node.py` and `anomaly.py` can both import them without risking a
circular import. Values are string literals matching the Mongo document
shapes described in docs/architecture.md §6, so the Milestone 3 repository
layer can persist these enums directly without a translation step.
"""

from enum import Enum


class LampStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class AnomalyType(str, Enum):
    SENSOR_OUT_OF_RANGE = "sensor_out_of_range"
    LAMP_OFFLINE = "lamp_offline"
    ACTUATOR_MISMATCH = "actuator_mismatch"
    TRAFFIC_SPIKE = "traffic_spike"


class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
