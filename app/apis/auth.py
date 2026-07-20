from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_active_user
from app.core.db.databases import async_get_db
from app.core.security.cookies import clear_refresh_token_cookie
from app.models.users import User
from app.schemas.auth import SignUpRequest, UserResponse
from app.schemas.common import DataResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Auth"],
)


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[UserResponse],
    summary="회원가입 API",
    description="사내 개발진, 의료 실무진, 연구진의 가입 신청을 처리합니다.",
)
async def signup(
    request: SignUpRequest,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> DataResponse[UserResponse]:
    user = await AuthService.signup(db=db, request=request)
    return DataResponse(data=UserResponse.model_validate(user))


@router.delete(
    "/signout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="회원탈퇴 API",
    description="본인 계정 정보 및 연관 데이터를 영구 삭제(Hard Delete)하고 토큰 쿠키를 삭제합니다.",
)
async def signout(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> None:
    await AuthService.signout(db=db, user=current_user)
    clear_refresh_token_cookie(response)
