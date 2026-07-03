"""
User entity — an authenticated principal with an RBAC role.

`password_hash` is always a hash (see app/security/password.py) — this
entity, and everything in the domain layer, never sees or stores a
plaintext password.
"""

from dataclasses import dataclass

from app.domain.entities.enums import Role


@dataclass(frozen=True)
class User:
    username: str
    password_hash: str
    role: Role
