"""
Unit tests for ProofOfWorkConsensus. Low difficulty throughout so mining
stays fast (a few hundred iterations at most). Pure logic, no infra.
"""

from datetime import datetime

import pytest

from app.infrastructure.blockchain.consensus import ProofOfWorkConsensus

pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 2, 14, 0, 0)


def test_mine_produces_a_hash_satisfying_is_valid():
    consensus = ProofOfWorkConsensus(difficulty=2)

    nonce, hash_ = consensus.mine(1, NOW, {"event_type": "genesis"}, "0" * 64)

    assert consensus.is_valid(hash_)
    assert isinstance(nonce, int)


def test_is_valid_rejects_hash_without_required_prefix():
    consensus = ProofOfWorkConsensus(difficulty=4)

    assert consensus.is_valid("f" * 64) is False


def test_is_valid_accepts_hash_with_required_prefix():
    consensus = ProofOfWorkConsensus(difficulty=3)

    assert consensus.is_valid("000abc" + "f" * 58) is True


def test_mining_is_deterministic_for_identical_inputs():
    consensus_a = ProofOfWorkConsensus(difficulty=2)
    consensus_b = ProofOfWorkConsensus(difficulty=2)

    result_a = consensus_a.mine(1, NOW, {"event_type": "genesis"}, "0" * 64)
    result_b = consensus_b.mine(1, NOW, {"event_type": "genesis"}, "0" * 64)

    assert result_a == result_b


def test_higher_difficulty_requires_more_leading_zeros():
    consensus = ProofOfWorkConsensus(difficulty=2)

    _, hash_ = consensus.mine(1, NOW, {"event_type": "genesis"}, "0" * 64)

    assert hash_.startswith("00")
