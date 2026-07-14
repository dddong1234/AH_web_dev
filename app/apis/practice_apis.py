# app/apis/practice_apis.py

import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator


router = APIRouter(
    prefix="/practice_api",
    tags=["Practice API"],
)

user_list = [
	{
		"id": 1,
		"name": "홍길동",
		"age": 24,
		"email": "gildong24@example.com",
		"password": "Password1234!!"
	},
	{
		"id": 2,
		"name": "장문복",
		"age": 21,
		"email": "moonluck12@example.com",
		"password": "Check1321!"
	},
	{
		"id": 3,
		"name": "임우진",
		"age": 31,
		"email": "limousine33@example.com",
		"password": "lwsPAssword12@"
	}
]

class UserUpdate(BaseModel):
    age: int | None = Field(
        default=None,
        ge=14,
    )
    email: str | None = Field(
        default=None,
        max_length=30,
    )
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=20,
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return value

        email_pattern = (
            r"^[A-Za-z0-9._%+-]+@"
            r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        )

        if not re.fullmatch(email_pattern, value):
            raise ValueError("올바른 이메일 형식이 아닙니다.")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        if value is None:
            return value

        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "비밀번호에는 대문자가 1개 이상 필요합니다."
            )

        if not re.search(r"[a-z]", value):
            raise ValueError(
                "비밀번호에는 소문자가 1개 이상 필요합니다."
            )

        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError(
                "비밀번호에는 특수문자가 1개 이상 필요합니다."
            )

        return value


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    user_data: UserUpdate,
):
    target_user = None

    for user in user_list:
        if user["id"] == user_id:
            target_user = user
            break

    if target_user is None:
        raise HTTPException(
            status_code=404,
            detail="해당 ID의 회원을 찾을 수 없습니다.",
        )

    update_data = user_data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="수정할 정보를 하나 이상 입력해야 합니다.",
        )

    target_user.update(update_data)

    return {
        "id": target_user["id"],
        "name": target_user["name"],
        "age": target_user["age"],
        "email": target_user["email"],
    }