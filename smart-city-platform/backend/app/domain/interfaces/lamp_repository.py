"""
LampRepository — persistence contract for LampNode.

A Protocol, not an ABC: the Mongo implementation (Milestone 3) satisfies
this structurally, with no inheritance coupling. Application-layer use
cases (Milestone 4) will depend on this interface, never on the concrete
Mongo class, so the domain/application layers stay Mongo-agnostic.
"""

from typing import Protocol

from app.domain.entities.lamp_node import LampNode


class LampRepository(Protocol):
    async def upsert(self, lamp: LampNode) -> None: ...

    async def get(self, device_id: str) -> LampNode | None: ...

    async def list_all(self) -> list[LampNode]: ...
