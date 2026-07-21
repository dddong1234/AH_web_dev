from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.exceptions import (
    AuthenticationRequiredError,
    InactiveUserError,
    PermissionDeniedError,
    UserNotFoundError,
)
from app.core.db.databases import async_get_db
from app.core.security.jwt import decode_access_token, get_user_id_from_payload
from app.models.enums import Role
from app.models.users import User
from app.repositories.auth_repository import AuthRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> User:
    if token is None:
        raise AuthenticationRequiredError()

    payload = decode_access_token(token)
    user_id = get_user_id_from_payload(payload)
    user = await AuthRepository.get_user_by_id(db=db, user_id=user_id)

    if user is None:
        raise UserNotFoundError()

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise InactiveUserError()

    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if current_user.role != Role.ADMIN:
        raise PermissionDeniedError()

    return current_user
