"""
Location entity — a lamp's fixed physical position, for map display.

Deliberately omitted from LampNode through M1-M6 ("has no home in the
domain entities yet" per lamp_repository.py's earlier docstring) since
nothing needed it until the Milestone 7 dashboard's map. Set at
seed/provisioning time, not editable via the API this milestone.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    lat: float
    lng: float
    label: str
