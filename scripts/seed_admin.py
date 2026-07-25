import asyncio
import os

from sqlalchemy import select

from app.core.db.databases import AsyncSessionLocal
from app.core.security.password import hash_password
from app.models.enums import Department, Gender, Role
from app.models.users import User


ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin1234!")


async def main() -> None:
    async with AsyncSessionLocal() as db:
        admin = await db.scalar(select(User).where(User.email == ADMIN_EMAIL))
        if admin is None:
            admin = User(
                email=ADMIN_EMAIL,
                name="개발 관리자",
                phone_number="01000000000",
                gender=Gender.M,
                department=Department.DEV,
                role=Role.ADMIN,
                is_active=True,
            )
            db.add(admin)

        admin.hashed_password = hash_password(ADMIN_PASSWORD)
        admin.role = Role.ADMIN
        admin.is_active = True
        await db.commit()
        print(f"Admin account ready: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
