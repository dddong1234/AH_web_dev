from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Department
from app.models.users import User


class AdminUserRepository:
    @staticmethod
    def _build_conditions(
        search: str | None,
        department: Department | None,
    ) -> list:
        conditions = []

        if search is not None and search.strip():
            search_pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    User.email.ilike(search_pattern),
                    User.name.ilike(search_pattern),
                )
            )

        if department is not None:
            conditions.append(User.department == department)

        return conditions

    @classmethod
    async def count_users(
        cls,
        db: AsyncSession,
        search: str | None,
        department: Department | None,
    ) -> int:
        conditions = cls._build_conditions(search, department)
        statement = select(func.count(User.id)).where(*conditions)
        result = await db.execute(statement)
        return result.scalar_one()

    @classmethod
    async def get_users(
        cls,
        db: AsyncSession,
        page: int,
        size: int,
        search: str | None,
        department: Department | None,
    ) -> list[User]:
        conditions = cls._build_conditions(search, department)
        statement = (
            select(User)
            .where(*conditions)
            .order_by(User.id.asc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: int,
    ) -> User | None:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

