import re
from fastapi import APIRouter
from pydantic import BaseModel, field_validator, Field

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

class UserSignUpRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=10)
    age: int = Field(..., ge=14)
    email: str = Field(..., max_length=30)
    password: str = Field(..., min_length=8, max_length=20)

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str):
        if not re.search(r'[A-Z]', password):
            raise ValueError('password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', password):
            raise ValueError('password must contain at least one lowercase letter')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError('password must contain at least one special character')
        return password

    @field_validator("email")
    @classmethod
    def validate_email(cls, email: str):
        if not re.search(r'@', email):
            raise ValueError('email must contain @')
        return email


@router.post(
    "/users",
    summary="회원 생성 API",
)
def create_user(user: UserSignUpRequest):
    new_id = max(
        (saved_user["id"] for saved_user in user_list), default=0
    ) + 1
    new_user = {
        "id": new_id,
        "name": user.name,
        "age": user.age,
        "email": user.email,
        "password": user.password,
    }
    user_list.append(new_user)
    return new_user