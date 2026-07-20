from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_admin_user
from app.core.db.databases import async_get_db
from app.models.enums import Department
from app.models.users import User
from app.schemas.admin_users import (
    AdminUserListResponse,
    RoleUpdateData,
    RoleUpdateRequest,
)
from app.schemas.common import DataResponse, ErrorResponse
from app.services.admin_user_service import AdminUserService


router = APIRouter(
    prefix="/api/v1/admin/users",
    tags=["Admin Users"],
)

DbSession = Annotated[AsyncSession, Depends(async_get_db)]
CurrentAdminUser = Annotated[User, Depends(get_current_admin_user)]


ERROR_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": "인증 실패",
    },
    403: {
        "model": ErrorResponse,
        "description": "관리자 권한 없음 또는 비활성 계정",
    },
    404: {
        "model": ErrorResponse,
        "description": "사용자 없음",
    },
    422: {
        "model": ErrorResponse,
        "description": "요청값 검증 실패",
    },
    500: {
        "model": ErrorResponse,
        "description": "서버 내부 오류",
    },
}


@router.get(
    "",
    summary="관리자 회원 목록 조회 API",
    response_model=AdminUserListResponse,
    responses=ERROR_RESPONSES,
)
async def get_admin_users(
    db: DbSession,
    _current_admin: CurrentAdminUser,
    page: Annotated[int, Query(ge=1, description="페이지 번호")] = 1,
    size: Annotated[
        int,
        Query(ge=1, le=100, description="페이지당 회원 수"),
    ] = 20,
    search: Annotated[
        str | None,
        Query(max_length=255, description="이메일 또는 이름 검색"),
    ] = None,
    department: Annotated[
        Department | None,
        Query(description="부서 필터"),
    ] = None,
) -> AdminUserListResponse:
    return await AdminUserService.get_users(
        db=db,
        page=page,
        size=size,
        search=search,
        department=department,
    )


@router.patch(
    "/{user_id}/role",
    summary="관리자 회원 권한 변경 API",
    response_model=DataResponse[RoleUpdateData],
    responses=ERROR_RESPONSES,
)
async def update_user_role(
    role_data: RoleUpdateRequest,
    db: DbSession,
    _current_admin: CurrentAdminUser,
    user_id: Annotated[int, Path(ge=1, description="권한 변경 대상 ID")],
) -> DataResponse[RoleUpdateData]:
    return await AdminUserService.update_role(
        db=db,
        user_id=user_id,
        role=role_data.role,
    )

