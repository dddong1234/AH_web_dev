from app.apis.auth import router as auth_router
from app.apis.practice_apis import router as practice_router

__all__ = [
    "auth_router",
    "practice_router",
]
