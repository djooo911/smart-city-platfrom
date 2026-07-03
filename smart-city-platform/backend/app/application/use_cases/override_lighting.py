"""
OverrideLightingUseCase — manual brightness override (operator+),
recorded on the blockchain as a config_change event with the acting
user and their stated reason.
"""

import dataclasses
from datetime import datetime

from app.application.use_cases._blockchain_helpers import load_or_create_chain
from app.domain.entities.lamp_node import LampNode
from app.domain.interfaces.blockchain_repository import BlockchainRepository
from app.domain.interfaces.lamp_repository import LampRepository


class OverrideLightingUseCase:
    def __init__(
        self, lamp_repository: LampRepository, blockchain_repository: BlockchainRepository
    ):
        self._lamp_repository = lamp_repository
        self._blockchain_repository = blockchain_repository

    async def execute(
        self,
        device_id: str,
        brightness_pct: float,
        actor: str,
        reason: str,
        now: datetime,
    ) -> LampNode:
        lamp = await self._lamp_repository.get(device_id)
        if lamp is None:
            raise ValueError(f"Unknown lamp: {device_id}")

        updated_lamp = dataclasses.replace(
            lamp, current_brightness_pct=brightness_pct, last_seen=now
        )
        await self._lamp_repository.upsert(updated_lamp)

        chain = await load_or_create_chain(self._blockchain_repository, now)
        block = chain.add_block(
            {
                "event_type": "config_change",
                "device_id": device_id,
                "actor": actor,
                "reason": reason,
                "brightness_pct": brightness_pct,
            },
            now,
        )
        await self._blockchain_repository.append_block(block)

        return updated_lamp
