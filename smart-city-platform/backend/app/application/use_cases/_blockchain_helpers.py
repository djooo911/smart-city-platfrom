"""
Shared helper for use cases that append blockchain events.

Not a use case itself -- extracted because IngestTelemetryUseCase,
OverrideLightingUseCase, and UpdateLampConfigUseCase all need the same
"load the chain, mining a genesis block on first use if none exists yet"
logic. Without this, `Blockchain(blocks=[])` raises (by design -- a chain
needs at least a genesis block), which every one of these use cases would
otherwise hit the very first time it runs against a fresh database.
"""

from datetime import datetime

from app.domain.interfaces.blockchain_repository import BlockchainRepository
from app.infrastructure.blockchain.chain import Blockchain, create_genesis_chain


async def load_or_create_chain(
    blockchain_repository: BlockchainRepository, now: datetime
) -> Blockchain:
    blocks = await blockchain_repository.load_chain()
    if not blocks:
        genesis_chain = create_genesis_chain(now)
        await blockchain_repository.append_block(genesis_chain.latest_block)
        return genesis_chain

    return Blockchain(blocks=blocks)
