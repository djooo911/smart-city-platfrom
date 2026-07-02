"""
Consensus strategy for mining/validating blocks.

`ConsensusStrategy` is a Protocol (per docs/architecture.md §7.2) so a
future Proof-of-Authority or multi-node strategy could be swapped in
without touching `Blockchain` — a stated design flex, not something to
build out now.

`ProofOfWorkConsensus.is_valid` is a cheap, algorithm-local acceptance
check (leading-zero prefix match). It does NOT recompute or authenticate
block contents — that composition (content-hash recompute + is_valid +
previous-hash linkage) is `Blockchain.verify_chain`'s job. Coupling content
recomputation into the consensus strategy would leak chain-structure
knowledge into an abstraction that's meant to know nothing about it (a
future PoA strategy's `is_valid` might check a signature, with no concept
of "leading zeros" at all).

Mining brute-forces the nonce from 0 upward with no iteration cap — at the
small difficulties this project uses (3-4), it converges fast in practice.
Not worth guarding with a max-iterations bound for academic scope.
"""

from datetime import datetime
from typing import Protocol

from app.infrastructure.blockchain.block import compute_block_hash

DEFAULT_DIFFICULTY = 4


class ConsensusStrategy(Protocol):
    def mine(
        self, index: int, timestamp: datetime, data: dict, previous_hash: str
    ) -> tuple[int, str]: ...

    def is_valid(self, hash_: str) -> bool: ...


class ProofOfWorkConsensus:
    def __init__(self, difficulty: int = DEFAULT_DIFFICULTY):
        self.difficulty = difficulty

    def mine(
        self, index: int, timestamp: datetime, data: dict, previous_hash: str
    ) -> tuple[int, str]:
        nonce = 0
        while True:
            candidate_hash = compute_block_hash(index, timestamp, data, previous_hash, nonce)
            if self.is_valid(candidate_hash):
                return nonce, candidate_hash
            nonce += 1

    def is_valid(self, hash_: str) -> bool:
        return hash_.startswith("0" * self.difficulty)
