from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.exceptions import (
    CurrentPasswordMismatchError,
    InvalidCredentialsError,
    PhoneNumberAlreadyExistsError,
)
from app.core.security.password import hash_password, verify_password
from app.models.users import User
from app.repositories.user_repository import UserRepository
from app.schemas.users import MyPageUpdateRequest, PasswordChangeRequest


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.repository = UserRepository(db)

    async def update_my_page(self, user: User, request: MyPageUpdateRequest) -> User:
        if request.phone_number is not None and request.phone_number != user.phone_number:
            existing = await self.repository.get_by_phone_number(request.phone_number)
            if existing is not None:
                raise PhoneNumberAlreadyExistsError()
            user.phone_number = request.phone_number
        if request.department is not None:
            user.department = request.department
        try:
            return await self.repository.save(user)
        except IntegrityError as exc:
            await self.repository.session.rollback()
            raise PhoneNumberAlreadyExistsError() from exc

    async def change_password(self, user: User, request: PasswordChangeRequest) -> None:
        if user.hashed_password is None:
            raise CurrentPasswordMismatchError()
        try:
            verify_password(request.current_password, user.hashed_password)
        except InvalidCredentialsError as exc:
            raise CurrentPasswordMismatchError() from exc
        user.hashed_password = hash_password(request.new_password)
        await self.repository.save(user)
