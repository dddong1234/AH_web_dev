from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.auth.exceptions import InvalidCredentialsError


password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> None:
    try:
        password_hasher.verify(hashed_password, password)
    except (InvalidHashError, VerifyMismatchError) as exc:
        raise InvalidCredentialsError() from exc
