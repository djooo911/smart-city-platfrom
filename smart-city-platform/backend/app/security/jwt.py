"""
JWT issuance/decoding — PyJWT, HS256. The one thing stdlib can't do, so
it's the sole new dependency this milestone adds.

Deliberately pure/stateless (no reach into `app.config.get_settings()`
internally, unlike most of this codebase's infrastructure) -- callers
supply `secret_key` explicitly. This mirrors the project's established
pattern of pure functions taking all their inputs explicitly (M1's rules
take `now`; M2's blockchain functions take explicit hash inputs) and
means these functions are trivially unit-testable with zero environment
setup, rather than requiring a `.env`/`SECRET_KEY` just to run
`pytest -m unit`.

Tokens embed `sub` (username) and `role` directly. `get_current_user`
(rbac.py) trusts these claims without a database round-trip per request —
see rbac.py's docstring for the tradeoff this implies.
"""

from datetime import datetime, timedelta, timezone

import jwt

from app.domain.entities.enums import Role

_ALGORITHM = "HS256"


def create_access_token(
    username: str, role: Role, secret_key: str, expires_minutes: int
) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": username, "role": role.value, "exp": expire_at}
    return jwt.encode(payload, secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> dict:
    return jwt.decode(token, secret_key, algorithms=[_ALGORITHM])
