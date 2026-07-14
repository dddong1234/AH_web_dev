import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from app.apis.practice_apis import user_list
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent

# 만약 static, media 폴더가 존재하지 않으면 생성
if not (BASE_DIR / "static").exists():
    os.mkdir(BASE_DIR / "static")
if not (BASE_DIR / "media").exists():
    os.mkdir(BASE_DIR / "media")

# 'static' 폴더를 '/static' 경로로 마운트 (CSS, JS 파일 서빙용)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
# 'media' 폴더를 '/media' 경로로 마운트 (사용자 업로드 파일 서빙용)
app.mount("/media", StaticFiles(directory=BASE_DIR / "media"), name="media")


@app.get(path="/healthcheck", status_code=200, include_in_schema=False)
async def healthcheck():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(BASE_DIR / "static" / "index.html")

# 특정 회원 조회 API (GET)
@app.get("/practice_api/users/{user_id}")
async def get_user(user_id: int):
    # 1. practice_apis.py에서 가져온 user_list를 순회하며 id를 비교합니다.
    for user in user_list:
        if user["id"] == user_id:
            # 2. 비밀번호를 제외한 정보만 돌려줍니다.
            return {
                "id": user["id"],
                "name": user["name"],
                "age": user["age"],
                "email": user["email"]
            }
            
    # 3. 일치하는 id가 없으면 404 Not Found 에러를 던집니다.
    raise HTTPException(status_code=404, detail="유효한 id가 아닙니다. 회원을 찾을 수 없습니다.")

# 회원 정보 삭제 API (DELETE)
@app.delete("/practice_api/users/{user_id}")
async def delete_user(user_id: int):
    for index, user in enumerate(user_list):
        if user["id"] == user_id:
            user_list.pop(index)
            return {"message": "회원 정보가 성공적으로 삭제되었습니다.", "deleted_id": user_id}
    raise HTTPException(status_code=404, detail="유효한 id가 아닙니다. 삭제할 회원을 찾을 수 없습니다.")


@app.get("/{path:path}", include_in_schema=False)
async def catch_all(path: str):
    # API나 정적 파일 경로는 제외 (FastAPI가 먼저 매칭하지 못한 경우에만 실행됨)
    if (
        path.startswith("api/v1")
        or path.startswith("static/")
        or path.startswith("media/")
    ):
        raise HTTPException(status_code=404)
    return FileResponse(BASE_DIR / "static" / "index.html")

