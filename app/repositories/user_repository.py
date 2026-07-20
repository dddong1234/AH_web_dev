from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_phone_number(self, phone_number: str) -> User | None:
        return await self.session.scalar(select(User).where(User.phone_number == phone_number))

    async def save(self, user: User) -> User:
        await self.session.commit()
        await self.session.refresh(user)
        return user
