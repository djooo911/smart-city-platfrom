"""
LampConfig entity.

Per-node thresholds used by both domain rules: energy optimization reads
the brightness bounds, anomaly detection reads the offline timeout and
actuator mismatch tolerance. Field names deliberately differ from the
`lamp_nodes.config` shape in docs/architecture.md §6.2 (which nests
thresholds under `anomaly_thresholds`) — reconciling the two is a Milestone
3 repository-mapping concern, not a domain-layer one.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LampConfig:
    min_brightness_pct: float = 10.0
    max_brightness_pct: float = 100.0
    offline_timeout_seconds: int = 60
    actuator_mismatch_tolerance_pct: float = 15.0
