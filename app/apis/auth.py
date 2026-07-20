from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.exceptions import RefreshTokenRequiredError
from app.core.db.databases import async_get_db
from app.core.security.constants import REFRESH_COOKIE_KEY
from app.core.security.cookies import set_refresh_token_cookie
from app.schemas.auth import LoginRequest, TokenPayload, TokenResponse
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Auth"],
)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
)
async def login(
    payload: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> TokenResponse:
    login_result = await AuthService.login(
        db=db,
        email=payload.email,
        password=payload.password,
    )
    set_refresh_token_cookie(response=response, refresh_token=login_result.refresh_token)

    return TokenResponse(
        data=TokenPayload(
            access_token=login_result.access_token,
            token_type=login_result.token_type,
            expires_in=login_result.expires_in,
        )
    )


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
)
async def refresh(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_KEY)] = None,
) -> TokenResponse:
    if refresh_token is None:
        raise RefreshTokenRequiredError()

    refresh_result = await AuthService.refresh(db=db, refresh_token=refresh_token)

    return TokenResponse(
        data=TokenPayload(
            access_token=refresh_result.access_token,
            token_type=refresh_result.token_type,
            expires_in=refresh_result.expires_in,
        )
    )
