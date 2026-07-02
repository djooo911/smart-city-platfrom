"""
BlockchainRepository — persistence contract for the blockchain ledger.

`load_chain` returns blocks ordered by index, ready to be handed directly
to `Blockchain(blocks=...)` (see infrastructure/blockchain/chain.py) to
reconstruct a validated in-memory chain.
"""

from typing import Protocol

from app.infrastructure.blockchain.block import Block


class BlockchainRepository(Protocol):
    async def append_block(self, block: Block) -> None: ...

    async def load_chain(self) -> list[Block]: ...
