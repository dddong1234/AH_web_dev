# app/apis/practice_apis.py
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

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/practice_api/users", tags=["Practice Users"])


# [API 2번] 특정 회원 조회
@router.get("/{user_id}")
async def get_user(user_id: int):
    for user in user_list:
        if user["id"] == user_id:
            return {
                "id": user["id"],
                "name": user["name"],
                "age": user["age"],
                "email": user["email"]
            }
    raise HTTPException(status_code=404, detail="유효한 id가 아닙니다.")


# [API 5번] 특정 회원 삭제
@router.delete("/{user_id}")
async def delete_user(user_id: int):
    for index, user in enumerate(user_list):
        if user["id"] == user_id:
            user_list.pop(index)
            return {"message": "회원 정보가 성공적으로 삭제되었습니다.", "deleted_id": user_id}
    raise HTTPException(status_code=404, detail="유효한 id가 아닙니다.")
