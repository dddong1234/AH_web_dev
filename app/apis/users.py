from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_active_user
from app.core.db.databases import async_get_db
from app.models.users import User
from app.schemas.common import DataResponse
from app.schemas.users import (
    MyPageResponse,
    MyPageUpdateRequest,
    PasswordChangeRequest,
    PasswordChangeResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me", response_model=DataResponse[MyPageResponse])
async def get_my_page(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DataResponse[MyPageResponse]:
    return DataResponse(data=MyPageResponse.model_validate(current_user))


@router.patch("/me", response_model=DataResponse[MyPageResponse])
async def update_my_page(
    request: MyPageUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> DataResponse[MyPageResponse]:
    user = await UserService(db).update_my_page(current_user, request)
    return DataResponse(data=MyPageResponse.model_validate(user))


@router.patch("/me/password", response_model=DataResponse[PasswordChangeResponse])
async def change_password(
    request: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> DataResponse[PasswordChangeResponse]:
    await UserService(db).change_password(current_user, request)
    return DataResponse(data=PasswordChangeResponse(message="비밀번호가 변경되었습니다."))
