"""
Integration tests for MongoUserRepository against a real MongoDB.
"""

import pytest

from app.domain.entities.enums import Role
from app.domain.entities.user import User
from app.infrastructure.mongo.repositories.user_repository import MongoUserRepository

pytestmark = pytest.mark.integration


def _user(**overrides) -> User:
    defaults = dict(username="user-test-001", password_hash="fake-hash", role=Role.VIEWER)
    defaults.update(overrides)
    return User(**defaults)


async def test_create_and_get_by_username_round_trip(db):
    repository = MongoUserRepository(db)
    user = _user()

    await repository.create(user)
    result = await repository.get_by_username(user.username)

    assert result == user


async def test_get_by_username_returns_none_for_unknown_user(db):
    repository = MongoUserRepository(db)

    assert await repository.get_by_username("does-not-exist") is None
