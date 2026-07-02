"""
Blockchain — an in-memory, tamper-evident chain of Blocks.

Pure in-memory engine, per Milestone 2 scope: no Mongo persistence (that's
Milestone 3, once a repository loads/saves blocks) and no FastAPI routes
(Milestone 4). The `Blockchain(blocks=[...])` constructor shape is
deliberate forward-compat: Milestone 3's Mongo repository will load
persisted blocks into a list and hand them to this exact constructor to
rehydrate a validated in-memory chain — no separate `from_blocks`
classmethod needed.

The constructor deliberately does NOT validate chain integrity — that's
what `verify_chain()` is for, explicitly separate from construction. This
is also what lets tests build a deliberately-broken chain (via
`Blockchain(blocks=[...tampered...])`) for `verify_chain()` to catch.
"""

from dataclasses import dataclass
from datetime import datetime

from app.infrastructure.blockchain.block import Block, compute_block_hash
from app.infrastructure.blockchain.consensus import ConsensusStrategy, ProofOfWorkConsensus

_GENESIS_PREVIOUS_HASH = "0" * 64
_GENESIS_DATA = {"event_type": "genesis"}


@dataclass(frozen=True)
class ChainVerificationResult:
    """
    `broken_at_index` reports the LOWEST index that fails any of
    verify_chain's three checks; scanning stops at the first break, since
    every block after a broken one is suspect anyway and scanning further
    would only add cascade-failure noise.
    """

    valid: bool
    broken_at_index: int | None


class Blockchain:
    def __init__(self, blocks: list[Block], consensus: ConsensusStrategy | None = None):
        if not blocks:
            raise ValueError("Blockchain requires at least a genesis block")
        self._blocks = list(blocks)
        self._consensus = consensus or ProofOfWorkConsensus()

    @property
    def blocks(self) -> tuple[Block, ...]:
        return tuple(self._blocks)

    @property
    def latest_block(self) -> Block:
        return self._blocks[-1]

    def add_block(self, data: dict, now: datetime) -> Block:
        previous = self.latest_block
        index = previous.index + 1
        nonce, hash_ = self._consensus.mine(index, now, data, previous.hash)
        block = Block(
            index=index,
            timestamp=now,
            data=data,
            previous_hash=previous.hash,
            nonce=nonce,
            hash=hash_,
        )
        self._blocks.append(block)
        return block

    def verify_chain(self) -> ChainVerificationResult:
        for i, block in enumerate(self._blocks):
            expected_hash = compute_block_hash(
                block.index, block.timestamp, block.data, block.previous_hash, block.nonce
            )
            if block.hash != expected_hash:
                return ChainVerificationResult(valid=False, broken_at_index=block.index)

            if not self._consensus.is_valid(block.hash):
                return ChainVerificationResult(valid=False, broken_at_index=block.index)

            if i > 0 and block.previous_hash != self._blocks[i - 1].hash:
                return ChainVerificationResult(valid=False, broken_at_index=block.index)

        return ChainVerificationResult(valid=True, broken_at_index=None)


def create_genesis_chain(
    now: datetime, consensus: ConsensusStrategy | None = None
) -> Blockchain:
    consensus = consensus or ProofOfWorkConsensus()
    nonce, hash_ = consensus.mine(0, now, _GENESIS_DATA, _GENESIS_PREVIOUS_HASH)
    genesis = Block(
        index=0,
        timestamp=now,
        data=_GENESIS_DATA,
        previous_hash=_GENESIS_PREVIOUS_HASH,
        nonce=nonce,
        hash=hash_,
    )
    return Blockchain(blocks=[genesis], consensus=consensus)
