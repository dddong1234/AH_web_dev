from fastapi import APIRouter
from pydantic import BaseModel


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


class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    email: str

# 1. 모든 회원의 정보를 목록으로 조회하는 API
@router.get(
    "/users",
    summary="전체 사용자 조회 API",
    response_model=list[UserResponse],
)
def get_users():
    return user_list