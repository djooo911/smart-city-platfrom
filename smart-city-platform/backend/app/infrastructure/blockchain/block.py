"""
Block — a single entry in the local blockchain ledger.

Fields mirror the `blockchain` collection in docs/architecture.md §7.1.
`compute_block_hash` is the single source of truth for what a block's hash
covers; both mining (consensus.py) and verification (chain.py) call it, so
they can never drift apart.

Canonicalization: `timestamp` is hashed via its explicit `.isoformat()`
string, never the raw `datetime` object or an implicit `str()` fallback —
naive and timezone-aware datetimes for "the same instant" serialize
differently, and that ambiguity would silently break hash reproducibility.
Callers are expected to pass a consistent datetime convention (naive or
aware) throughout a chain's lifetime; this module does not normalize it.

`default=str` on the outer `json.dumps` is kept only as a defensive
fallback for a stray non-JSON-native value nested inside `data` (event
payload schemas aren't owned by this milestone) — it is not the mechanism
used for `timestamp` itself.

Note: Python's float repr is stable within a given Python/json version but
isn't formally guaranteed across versions — a latent, documented limitation
if `data` ever carries floats, not something M2 guards against.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Block:
    index: int
    timestamp: datetime
    data: dict
    previous_hash: str
    nonce: int
    hash: str


def compute_block_hash(
    index: int, timestamp: datetime, data: dict, previous_hash: str, nonce: int
) -> str:
    payload = {
        "index": index,
        "timestamp": timestamp.isoformat(),
        "data": data,
        "previous_hash": previous_hash,
        "nonce": nonce,
    }
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
