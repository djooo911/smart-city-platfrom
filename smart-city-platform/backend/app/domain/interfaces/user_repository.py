"""
UserRepository — persistence contract for User.
"""

from typing import Protocol

from app.domain.entities.user import User


class UserRepository(Protocol):
    async def get_by_username(self, username: str) -> User | None: ...

    async def create(self, user: User) -> None: ...
