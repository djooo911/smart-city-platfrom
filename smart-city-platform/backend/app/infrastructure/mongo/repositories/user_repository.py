"""
MongoUserRepository — Mongo-backed implementation of UserRepository.

`_id` = username, mirroring MongoLampRepository's pattern (a natural
human-meaningful key, not an ObjectId).
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.entities.enums import Role
from app.domain.entities.user import User

_COLLECTION_NAME = "users"


def _to_document(user: User) -> dict:
    return {"password_hash": user.password_hash, "role": user.role.value}


def _to_entity(doc: dict) -> User:
    return User(username=doc["_id"], password_hash=doc["password_hash"], role=Role(doc["role"]))


class MongoUserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db[_COLLECTION_NAME]

    async def get_by_username(self, username: str) -> User | None:
        doc = await self._collection.find_one({"_id": username})
        return _to_entity(doc) if doc else None

    async def create(self, user: User) -> None:
        await self._collection.insert_one({"_id": user.username, **_to_document(user)})
