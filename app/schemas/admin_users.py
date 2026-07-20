from pydantic import BaseModel, ConfigDict

from app.models.enums import Department, Gender, Role


class AdminUserResponse(BaseModel):
    """관리자 회원 목록에 표시할 사용자 정보."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str | None
    name: str | None
    department: Department
    gender: Gender
    phone_number: str | None
    role: Role
    is_active: bool


class PaginationResponse(BaseModel):
    page: int
    size: int
    total: int
    total_pages: int


class AdminUserListResponse(BaseModel):
    data: list[AdminUserResponse]
    pagination: PaginationResponse


class RoleUpdateRequest(BaseModel):
    role: Role


class RoleUpdateData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str | None
    name: str | None
    role: Role

