from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.exceptions import InactiveUserError, InvalidCredentialsError
from app.core.config import settings
from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    get_refresh_token_expires_at,
    hash_token,
)
from app.core.security.password import verify_password
from app.repositories.auth_repository import AuthRepository


@dataclass
class LoginResult:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class AuthService:
    @staticmethod
    async def login(db: AsyncSession, email: str, password: str) -> LoginResult:
        user = await AuthRepository.get_user_by_email(db=db, email=email)

        if user is None or user.hashed_password is None:
            raise InvalidCredentialsError()

        verify_password(password=password, hashed_password=user.hashed_password)

        if not user.is_active:
            raise InactiveUserError()

        access_token = create_access_token(user_id=user.id)
        refresh_token = create_refresh_token(user_id=user.id)

        await AuthRepository.create_refresh_token(
            db=db,
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=get_refresh_token_expires_at(),
        )
        await db.commit()

        return LoginResult(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
