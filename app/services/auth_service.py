from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.exceptions import (
    EmailAlreadyExistsError,
    PhoneNumberAlreadyExistsError,
)
from app.core.security.password import hash_password
from app.models.users import User
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import SignUpRequest


class AuthService:
    @staticmethod
    async def signup(db: AsyncSession, request: SignUpRequest) -> User:
        # 1. 이메일 중복 검사
        existing_email_user = await AuthRepository.get_user_by_email(db=db, email=request.email)
        if existing_email_user is not None:
            raise EmailAlreadyExistsError()

        # 2. 휴대폰 번호 중복 검사
        existing_phone_user = await AuthRepository.get_user_by_phone_number(
            db=db, phone_number=request.phone_number
        )
        if existing_phone_user is not None:
            raise PhoneNumberAlreadyExistsError()

        # 3. 비밀번호 Argon2 해시 생성 (NFR-USER-002)
        hashed_pw = hash_password(request.password)

        # 4. 사용자 생성 및 저장
        user = await AuthRepository.create_user(
            db=db,
            email=request.email,
            hashed_password=hashed_pw,
            name=request.name,
            department=request.department,
            gender=request.gender,
            phone_number=request.phone_number,
        )
        await db.commit()
        return user

    @staticmethod
    async def signout(db: AsyncSession, user: User) -> None:
        # 사용자 데이터 영구 삭제 (Cascade 설정에 의해 하위 데이터 자동 삭제)
        await AuthRepository.delete_user(db=db, user=user)
        await db.commit()
