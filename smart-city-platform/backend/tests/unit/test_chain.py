"""
Unit tests for Blockchain / create_genesis_chain / verify_chain. Low PoW
difficulty throughout so mining stays fast. Pure logic, no infra.
"""

import dataclasses
from datetime import datetime

import pytest

from app.infrastructure.blockchain.block import compute_block_hash
from app.infrastructure.blockchain.chain import Blockchain, create_genesis_chain
from app.infrastructure.blockchain.consensus import ProofOfWorkConsensus

pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 2, 14, 0, 0)
LATER = datetime(2026, 7, 2, 14, 5, 0)
EVEN_LATER = datetime(2026, 7, 2, 14, 10, 0)


def _consensus() -> ProofOfWorkConsensus:
    return ProofOfWorkConsensus(difficulty=2)


def _three_block_chain() -> Blockchain:
    consensus = _consensus()
    chain = create_genesis_chain(NOW, consensus=consensus)
    chain.add_block({"event_type": "anomaly_detected", "device_id": "lamp-001"}, LATER)
    chain.add_block({"event_type": "config_change", "device_id": "lamp-002"}, EVEN_LATER)
    return chain


def test_create_genesis_chain_has_one_valid_block():
    chain = create_genesis_chain(NOW, consensus=_consensus())

    assert len(chain.blocks) == 1
    assert chain.latest_block.index == 0
    assert chain.latest_block.previous_hash == "0" * 64


def test_add_block_grows_the_chain_and_links_correctly():
    chain = create_genesis_chain(NOW, consensus=_consensus())
    genesis_hash = chain.latest_block.hash

    new_block = chain.add_block({"event_type": "lamp_failure"}, LATER)

    assert len(chain.blocks) == 2
    assert new_block.index == 1
    assert new_block.previous_hash == genesis_hash
    assert chain.latest_block == new_block


def test_verify_chain_valid_on_untampered_multi_block_chain():
    chain = _three_block_chain()

    result = chain.verify_chain()

    assert result.valid is True
    assert result.broken_at_index is None


def test_blocks_property_returns_a_defensive_copy():
    chain = create_genesis_chain(NOW, consensus=_consensus())

    blocks = chain.blocks
    assert isinstance(blocks, tuple)


def test_constructor_rejects_empty_block_list():
    with pytest.raises(ValueError):
        Blockchain(blocks=[])


# --- tamper detection -------------------------------------------------------------


def test_verify_chain_detects_tampered_data_without_hash_recompute():
    chain = _three_block_chain()
    blocks = list(chain.blocks)

    tampered = dataclasses.replace(blocks[1], data={"event_type": "config_change"})
    blocks[1] = tampered
    tampered_chain = Blockchain(blocks=blocks, consensus=_consensus())

    result = tampered_chain.verify_chain()

    assert result.valid is False
    assert result.broken_at_index == 1


def test_verify_chain_detects_broken_previous_hash_linkage():
    chain = _three_block_chain()
    blocks = list(chain.blocks)

    tampered = dataclasses.replace(blocks[2], previous_hash="f" * 64)
    blocks[2] = tampered
    tampered_chain = Blockchain(blocks=blocks, consensus=_consensus())

    result = tampered_chain.verify_chain()

    assert result.valid is False
    assert result.broken_at_index == 2


def test_verify_chain_detects_hash_that_never_went_through_consensus():
    # Recompute a self-consistent hash for tampered content (so the content
    # check alone would pass), but at a difficulty the block was never
    # actually mined at -- proves verify_chain's is_valid check is load
    # bearing, not a dead third check.
    chain = _three_block_chain()
    blocks = list(chain.blocks)
    block = blocks[1]

    forged_data = {"event_type": "forged"}
    forged_hash = compute_block_hash(
        block.index, block.timestamp, forged_data, block.previous_hash, nonce=0
    )
    # nonce=0 is extremely unlikely to satisfy difficulty=2 by chance.
    consensus = _consensus()
    assert not consensus.is_valid(forged_hash)

    forged_block = dataclasses.replace(block, data=forged_data, nonce=0, hash=forged_hash)
    blocks[1] = forged_block
    tampered_chain = Blockchain(blocks=blocks, consensus=consensus)

    result = tampered_chain.verify_chain()

    assert result.valid is False
    assert result.broken_at_index == 1
