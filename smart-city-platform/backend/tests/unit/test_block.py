"""
Unit tests for compute_block_hash. Pure logic, no infra.
"""

from datetime import datetime

import pytest

from app.infrastructure.blockchain.block import compute_block_hash

pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 2, 14, 0, 0)


def _hash(**overrides) -> str:
    defaults = dict(
        index=1,
        timestamp=NOW,
        data={"event_type": "anomaly_detected"},
        previous_hash="a" * 64,
        nonce=42,
    )
    defaults.update(overrides)
    return compute_block_hash(**defaults)


def test_hash_is_deterministic_for_identical_inputs():
    assert _hash() == _hash()


def test_hash_is_a_sha256_hex_digest():
    result = _hash()

    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_changing_index_changes_the_hash():
    assert _hash(index=1) != _hash(index=2)


def test_changing_timestamp_changes_the_hash():
    assert _hash(timestamp=NOW) != _hash(timestamp=datetime(2026, 7, 2, 14, 0, 1))


def test_changing_data_changes_the_hash():
    assert _hash(data={"event_type": "anomaly_detected"}) != _hash(
        data={"event_type": "lamp_failure"}
    )


def test_changing_previous_hash_changes_the_hash():
    assert _hash(previous_hash="a" * 64) != _hash(previous_hash="b" * 64)


def test_changing_nonce_changes_the_hash():
    assert _hash(nonce=42) != _hash(nonce=43)


def test_data_key_order_does_not_affect_the_hash():
    hash_a = _hash(data={"a": 1, "b": 2})
    hash_b = _hash(data={"b": 2, "a": 1})

    assert hash_a == hash_b
