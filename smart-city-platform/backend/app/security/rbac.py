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

Uses `HTTPBearer`, not `OAuth2PasswordBearer`: `/auth/login` takes a JSON
body (see schemas/auth.py's LoginRequest), not an OAuth2 password-grant
form -- OAuth2PasswordBearer tells Swagger UI's "Authorize" button to
submit a form-encoded username/password to the token URL, which doesn't
match our actual login contract and fails with a 422. HTTPBearer instead
gives Swagger a plain "paste your token" field: call POST /auth/login
manually via "Try it out", copy the returned access_token, then
Authorize with that.
"""

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.domain.entities.enums import Role
from app.security.jwt import decode_access_token

http_bearer = HTTPBearer(auto_error=False)

_ROLE_RANK = {Role.VIEWER: 0, Role.OPERATOR: 1, Role.ADMIN: 2}


@dataclass(frozen=True)
class CurrentUser:
    username: str
    role: Role


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> CurrentUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        # auto_error=False so a missing/malformed Authorization header lands
        # here as None instead of HTTPBearer's default 403 -- a request with
        # no credentials at all is a 401 (unauthenticated), not a 403
        # (authenticated but forbidden).
        raise credentials_error
    try:
        payload = decode_access_token(credentials.credentials, get_settings().secret_key)
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
