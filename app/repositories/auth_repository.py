from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Department, Gender, Role
from app.models.refresh_tokens import RefreshToken
from app.models.users import User


class AuthRepository:
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_phone_number(db: AsyncSession, phone_number: str) -> User | None:
        stmt = select(User).where(User.phone_number == phone_number)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        hashed_password: str,
        name: str,
        department: Department,
        gender: Gender,
        phone_number: str,
        role: Role = Role.PENDING,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            name=name,
            department=department,
            gender=gender,
            phone_number=phone_number,
            role=role,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user: User) -> None:
        await db.delete(user)
        await db.flush()

    @staticmethod
    async def create_refresh_token(
        db: AsyncSession,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(refresh_token)
        await db.flush()
        return refresh_token

    @staticmethod
    async def get_refresh_token_by_hash(
        db: AsyncSession,
        token_hash: str,
    ) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def revoke_refresh_token(
        db: AsyncSession,
        refresh_token: RefreshToken,
    ) -> RefreshToken:
        refresh_token.revoked_at = datetime.now(KST).replace(tzinfo=None)
        await db.flush()
        return refresh_token
