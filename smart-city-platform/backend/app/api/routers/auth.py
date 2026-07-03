"""
Authentication: POST /auth/login issues a JWT (see app/security/jwt.py)
used as a Bearer token on every subsequent authenticated request.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_authenticate_user_use_case
from app.api.schemas.auth import LoginRequest
from app.application.use_cases.authenticate_user import AuthenticateUserUseCase

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    body: LoginRequest,
    use_case: AuthenticateUserUseCase = Depends(get_authenticate_user_use_case),
) -> dict:
    token = await use_case.execute(body.username, body.password)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    return {"data": {"access_token": token, "token_type": "bearer"}, "meta": {}}
