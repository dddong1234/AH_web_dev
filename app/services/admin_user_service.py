from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.exceptions import AppBaseException
from app.models.enums import Department, Role
from app.repositories.admin_user_repository import AdminUserRepository
from app.schemas.admin_users import (
    AdminUserListResponse,
    AdminUserResponse,
    PaginationResponse,
    RoleUpdateData,
)
from app.schemas.common import DataResponse

class AdminUserNotFoundError(AppBaseException):
    status_code = 404
    code = "USER_NOT_FOUND"
    message = "사용자를 찾을 수 없습니다."

class AdminUserService:
    @staticmethod
    async def get_users(
        db: AsyncSession,
        page: int,
        size: int,
        search: str | None,
        department: Department | None,
    ) -> AdminUserListResponse:
        try:
            total = await AdminUserRepository.count_users(
                db=db,
                search=search,
                department=department,
            )
            users = await AdminUserRepository.get_users(
                db=db,
                page=page,
                size=size,
                search=search,
                department=department,
            )
        except SQLAlchemyError as exc:
            raise AppBaseException() from exc

        total_pages = (total + size - 1) // size if total else 0

        return AdminUserListResponse(
            data=[AdminUserResponse.model_validate(user) for user in users],
            pagination=PaginationResponse(
                page=page,
                size=size,
                total=total,
                total_pages=total_pages,
            ),
        )

    @staticmethod
    async def update_role(
        db: AsyncSession,
        user_id: int,
        role: Role,
    ) -> DataResponse[RoleUpdateData]:
        try:
            target_user = await AdminUserRepository.get_user_by_id(
                db=db,
                user_id=user_id,
            )

            if target_user is None:
                raise AdminUserNotFoundError()

            target_user.role = role
            await db.commit()
            await db.refresh(target_user)
        except AdminUserNotFoundError:
            raise
        except SQLAlchemyError as exc:
            await db.rollback()
            raise AppBaseException() from exc

        return DataResponse(
            data=RoleUpdateData.model_validate(target_user)
        )

