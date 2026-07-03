"""
MongoBlockchainRepository — Mongo-backed implementation of
BlockchainRepository.

Field mapping is 1:1 with docs/architecture.md §6.5 (Mongo assigns its own
ObjectId `_id`; `index` is the chain-position field used for ordering and
uniqueness, per infrastructure/mongo/indexes.py).

Datetime correctness note: Block.hash is only reproducible if
`timestamp` round-trips through Mongo with the same naive/aware
convention it was mined with (see block.py's docstring). This repository
relies on Motor/PyMongo's default behavior -- naive UTC datetimes in,
naive UTC datetimes out (no `tz_aware=True` anywhere in this codebase's
Mongo client setup) -- rather than doing any manual conversion, so the
save -> load round-trip preserves hash validity. Covered by
tests/integration/test_blockchain_repository.py, which mines a chain,
round-trips it through Mongo, and asserts `verify_chain()` still reports
valid.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.infrastructure.blockchain.block import Block

_COLLECTION_NAME = "blockchain"


def _to_document(block: Block) -> dict:
    return {
        "index": block.index,
        "timestamp": block.timestamp,
        "data": block.data,
        "previous_hash": block.previous_hash,
        "nonce": block.nonce,
        "hash": block.hash,
    }


def _to_entity(doc: dict) -> Block:
    return Block(
        index=doc["index"],
        timestamp=doc["timestamp"],
        data=doc["data"],
        previous_hash=doc["previous_hash"],
        nonce=doc["nonce"],
        hash=doc["hash"],
    )


class MongoBlockchainRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db[_COLLECTION_NAME]

    async def append_block(self, block: Block) -> None:
        await self._collection.insert_one(_to_document(block))

    async def load_chain(self) -> list[Block]:
        cursor = self._collection.find({}).sort("index", 1)
        return [_to_entity(doc) async for doc in cursor]

    async def get_block_by_index(self, index: int) -> Block | None:
        doc = await self._collection.find_one({"index": index})
        return _to_entity(doc) if doc else None

    async def list_by_device(self, device_id: str) -> list[Block]:
        cursor = self._collection.find({"data.device_id": device_id}).sort("index", 1)
        return [_to_entity(doc) async for doc in cursor]
