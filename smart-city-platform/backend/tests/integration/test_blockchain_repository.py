"""
Integration tests for MongoBlockchainRepository against a real MongoDB.

The `verify_chain` round-trip test is the highest-risk correctness check
in Milestone 3: if Mongo's datetime handling ever drifted from the naive-
UTC convention Milestone 2's hashing relies on, every historical block
would report as tampered purely from representation drift, not real
tampering.
"""

from datetime import datetime

import pytest

from app.infrastructure.blockchain.chain import Blockchain, create_genesis_chain
from app.infrastructure.blockchain.consensus import ProofOfWorkConsensus
from app.infrastructure.mongo.repositories.blockchain_repository import MongoBlockchainRepository

pytestmark = pytest.mark.integration

NOW = datetime(2026, 7, 3, 10, 0, 0)
LATER = datetime(2026, 7, 3, 10, 5, 0)
EVEN_LATER = datetime(2026, 7, 3, 10, 10, 0)


def _consensus() -> ProofOfWorkConsensus:
    return ProofOfWorkConsensus(difficulty=2)


async def test_append_and_load_chain_round_trip(db):
    repository = MongoBlockchainRepository(db)
    consensus = _consensus()
    chain = create_genesis_chain(NOW, consensus=consensus)
    chain.add_block({"event_type": "anomaly_detected", "device_id": "lamp-001"}, LATER)
    chain.add_block({"event_type": "config_change", "device_id": "lamp-002"}, EVEN_LATER)

    for block in chain.blocks:
        await repository.append_block(block)

    loaded_blocks = await repository.load_chain()

    assert list(loaded_blocks) == list(chain.blocks)


async def test_loaded_chain_passes_verify_chain(db):
    repository = MongoBlockchainRepository(db)
    consensus = _consensus()
    chain = create_genesis_chain(NOW, consensus=consensus)
    chain.add_block({"event_type": "lamp_failure", "device_id": "lamp-003"}, LATER)

    for block in chain.blocks:
        await repository.append_block(block)

    loaded_blocks = await repository.load_chain()
    reconstructed_chain = Blockchain(blocks=loaded_blocks, consensus=consensus)

    result = reconstructed_chain.verify_chain()

    assert result.valid is True
    assert result.broken_at_index is None


async def test_load_chain_returns_blocks_ordered_by_index(db):
    repository = MongoBlockchainRepository(db)
    consensus = _consensus()
    chain = create_genesis_chain(NOW, consensus=consensus)
    chain.add_block({"event_type": "system_alert"}, LATER)
    chain.add_block({"event_type": "config_change"}, EVEN_LATER)

    # Insert out of order to prove load_chain sorts, not just returns insertion order.
    for block in reversed(chain.blocks):
        await repository.append_block(block)

    loaded_blocks = await repository.load_chain()

    assert [block.index for block in loaded_blocks] == [0, 1, 2]


async def test_load_chain_returns_empty_list_when_no_blocks(db):
    repository = MongoBlockchainRepository(db)

    assert await repository.load_chain() == []
