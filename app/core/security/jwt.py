from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.auth.exceptions import (
    AccessTokenExpiredError,
    InvalidAccessTokenError,
    InvalidRefreshTokenError,
    RefreshTokenExpiredError,
)
from app.core.config import settings
from app.core.security.constants import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    TOKEN_TYPE_CLAIM,
    USER_ID_CLAIM,
)


def create_access_token(user_id: int) -> str:
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(user_id=user_id, token_type=ACCESS_TOKEN_TYPE, expires_delta=expires_delta)


def create_refresh_token(user_id: int) -> str:
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(user_id=user_id, token_type=REFRESH_TOKEN_TYPE, expires_delta=expires_delta)


def decode_access_token(token: str) -> dict[str, Any]:
    payload = _decode_token(token=token, expired_exception=AccessTokenExpiredError, invalid_exception=InvalidAccessTokenError)
    _validate_token_type(payload=payload, expected_token_type=ACCESS_TOKEN_TYPE, invalid_exception=InvalidAccessTokenError)
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    payload = _decode_token(token=token, expired_exception=RefreshTokenExpiredError, invalid_exception=InvalidRefreshTokenError)
    _validate_token_type(payload=payload, expected_token_type=REFRESH_TOKEN_TYPE, invalid_exception=InvalidRefreshTokenError)
    return payload


def get_user_id_from_payload(payload: dict[str, Any]) -> int:
    user_id = payload.get(USER_ID_CLAIM)
    if not isinstance(user_id, int):
        raise InvalidAccessTokenError()
    return user_id


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


KST = timezone(timedelta(hours=9))


def get_refresh_token_expires_at() -> datetime:
    expires_at = datetime.now(KST) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return expires_at.replace(tzinfo=None)


def _create_token(user_id: int, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(KST)
    payload = {
        USER_ID_CLAIM: user_id,
        TOKEN_TYPE_CLAIM: token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode_token(
    token: str,
    expired_exception: type[Exception],
    invalid_exception: type[Exception],
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise expired_exception() from exc
    except jwt.InvalidTokenError as exc:
        raise invalid_exception() from exc

    if not isinstance(payload, dict):
        raise invalid_exception()
    return payload


def _validate_token_type(
    payload: dict[str, Any],
    expected_token_type: str,
    invalid_exception: type[Exception],
) -> None:
    token_type = payload.get(TOKEN_TYPE_CLAIM)
    if token_type != expected_token_type:
        raise invalid_exception()
