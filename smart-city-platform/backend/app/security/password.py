"""
Password hashing — stdlib `hashlib.pbkdf2_hmac`, no passlib/bcrypt
dependency (consistent with the blockchain engine's stdlib-first hashing
in Milestone 2). PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP's 2023
minimum recommendation for PBKDF2-SHA256) and a random 16-byte salt per
password.

Stored format: "<iterations>$<salt_hex>$<hash_hex>" — self-describing, so
a future iteration-count bump doesn't invalidate hashes already stored
with the old count.
"""

import hashlib
import hmac
import secrets

_ALGORITHM = "sha256"
_ITERATIONS = 600_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_hex(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        _ALGORITHM, password.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS
    )
    return f"{_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        iterations_str, salt, expected_hex = password_hash.split("$")
        iterations = int(iterations_str)
    except ValueError:
        return False

    digest = hashlib.pbkdf2_hmac(
        _ALGORITHM, password.encode("utf-8"), bytes.fromhex(salt), iterations
    )
    return hmac.compare_digest(digest.hex(), expected_hex)
