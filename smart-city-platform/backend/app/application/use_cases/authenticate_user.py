"""
AuthenticateUserUseCase — verifies credentials and issues a JWT.

Keeps the auth router thin: it never touches password.py/jwt.py directly.
"""

from app.config import get_settings
from app.domain.interfaces.user_repository import UserRepository
from app.security.jwt import create_access_token
from app.security.password import verify_password


class AuthenticateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def execute(self, username: str, password: str) -> str | None:
        user = await self._user_repository.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            return None

        settings = get_settings()
        return create_access_token(
            user.username, user.role, settings.secret_key, settings.access_token_expire_minutes
        )
