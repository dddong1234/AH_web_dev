import re

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator

from app.models.enums import Department, Gender, Role


class MyPageResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    department: Department
    gender: Gender
    phone_number: str
    role: Role
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class MyPageUpdateRequest(BaseModel):
    department: Department | None = None
    phone_number: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone_number(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.replace("-", "")
            if not re.fullmatch(r"010\d{8}", value):
                raise ValueError("휴대폰 번호는 010으로 시작하는 11자리 숫자여야 합니다.")
        return value

    @model_validator(mode="after")
    def ensure_at_least_one_field(self) -> "MyPageUpdateRequest":
        if self.department is None and self.phone_number is None:
            raise ValueError("수정할 항목을 하나 이상 입력해야 합니다.")
        return self


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    model_config = ConfigDict(extra="forbid")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if (
            len(value) < 8
            or re.search(r"[A-Za-z]", value) is None
            or re.search(r"\d", value) is None
            or re.search(r"[^A-Za-z0-9]", value) is None
        ):
            raise ValueError("비밀번호는 8자 이상이며 영문, 숫자, 특수문자를 각각 포함해야 합니다.")
        return value


class PasswordChangeResponse(BaseModel):
    message: str
