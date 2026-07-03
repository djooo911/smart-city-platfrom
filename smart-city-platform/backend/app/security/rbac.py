"""
Authentication + role-gating dependencies for FastAPI routes.

`get_current_user` decodes and trusts the JWT's `sub`/`role` claims
directly -- no UserRepository round-trip per request. This means a role
change or account deletion doesn't take effect until the token expires
(default 60 minutes). That's an accepted tradeoff for this project's
scope, not an oversight: revisiting it (e.g. a revocation list) would be
a real productionization item.

`CurrentUser` is deliberately NOT the domain `User` entity -- `User`
carries `password_hash`, which has no meaningful value here (we never
re-fetch the stored hash for an already-authenticated request), and
routes only ever need `username`/`role` for RBAC checks and "acted_by"
audit fields.
"""

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import get_settings
from app.domain.entities.enums import Role
from app.security.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{get_settings().api_v1_prefix}/auth/login")

_ROLE_RANK = {Role.VIEWER: 0, Role.OPERATOR: 1, Role.ADMIN: 2}


@dataclass(frozen=True)
class CurrentUser:
    username: str
    role: Role


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token, get_settings().secret_key)
        username = payload["sub"]
        role = Role(payload["role"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise credentials_error

    return CurrentUser(username=username, role=role)


def require_role(minimum: Role):
    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if _ROLE_RANK[current_user.role] < _ROLE_RANK[minimum]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {minimum.value}+ role",
            )
        return current_user

    return dependency
