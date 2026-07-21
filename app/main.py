import os
from pathlib import Path

from fastapi import FastAPI
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from app.apis.admin_users import router as admin_users_router
from app.apis.auth import router as auth_router
from app.apis.patients import router as patients_router
from app.apis.practice_apis import router as practice_router
from app.apis.users import router as users_router
from app.core.auth import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
app.include_router(auth_router)
app.include_router(practice_router)
app.include_router(users_router)
app.include_router(admin_users_router)
app.include_router(patients_router)

BASE_DIR = Path(__file__).resolve().parent.parent

if not (BASE_DIR / "static").exists():
    os.mkdir(BASE_DIR / "static")
if not (BASE_DIR / "media").exists():
    os.mkdir(BASE_DIR / "media")
if not (BASE_DIR / "uploads").exists():
    os.mkdir(BASE_DIR / "uploads")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/media", StaticFiles(directory=BASE_DIR / "media"), name="media")
app.mount("/uploads", StaticFiles(directory=BASE_DIR / "uploads"), name="uploads")


@app.get(path="/healthcheck", status_code=200, include_in_schema=False)
async def healthcheck():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/{path:path}", include_in_schema=False)
async def catch_all(path: str):
    if (
        path.startswith("api/v1")
        or path.startswith("static/")
        or path.startswith("media/")
        or path.startswith("uploads/")
    ):
        from fastapi import HTTPException

        raise HTTPException(status_code=404)
    return FileResponse(BASE_DIR / "static" / "index.html")
