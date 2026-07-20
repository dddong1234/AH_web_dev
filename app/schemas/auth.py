from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class TokenPayload(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenResponse(BaseModel):
    data: TokenPayload


class MessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
