from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.auth.exceptions import RefreshTokenRequiredError
from app.core.db.databases import async_get_db
from app.core.security.constants import REFRESH_COOKIE_KEY
from app.core.security.cookies import clear_refresh_token_cookie, set_refresh_token_cookie
from app.models.users import User
from app.schemas.auth import (
    LoginRequest,
    SignUpRequest,
    TokenPayload,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import DataResponse
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Auth"],
)


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[UserResponse],
)
async def signup(
    request: SignUpRequest,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> DataResponse[UserResponse]:
    user = await AuthService.signup(db=db, request=request)
    return DataResponse(data=UserResponse.model_validate(user))


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


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    response: Response,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_KEY)] = None,
) -> Response:
    await AuthService.logout(db=db, refresh_token=refresh_token)
    clear_refresh_token_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.delete(
    "/signout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def signout(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> None:
    await AuthService.signout(db=db, user=current_user)
    clear_refresh_token_cookie(response)
