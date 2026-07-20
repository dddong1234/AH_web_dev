import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import Department, Gender, Role


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2, max_length=20)
    department: Department
    gender: Gender
    phone_number: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        # NFR-USER-002: 최소 8자 이상, 영문, 숫자, 특수문자를 각각 1개 이상 포함
        pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]).{8,}$"
        if not re.match(pattern, value):
            raise ValueError("비밀번호는 8자 이상이며 영문, 숫자, 특수문자를 각각 포함해야 합니다.")
        return value

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone_number(cls, value: str) -> str:
        if isinstance(value, str):
            cleaned = re.sub(r"\D", "", value)
            if len(cleaned) != 11 or not cleaned.startswith("010"):
                raise ValueError("휴대폰 번호는 010으로 시작하는 11자리 숫자여야 합니다.")
            return cleaned
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    department: Department
    gender: Gender
    phone_number: str
    role: Role
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenResponse(BaseModel):
    data: TokenPayload


class MessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
