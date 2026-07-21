from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Gender
from app.models.patients import Patients


class PatientRepository:
    @staticmethod
    def _build_conditions(
        *,
        name: str | None,
        gender: Gender | None,
        min_age: int | None,
        max_age: int | None,
    ) -> list:
        conditions = []

        if name:
            conditions.append(Patients.name.ilike(f"%{name}%"))
        if gender is not None:
            conditions.append(Patients.gender == gender)
        if min_age is not None:
            conditions.append(Patients.age >= min_age)
        if max_age is not None:
            conditions.append(Patients.age <= max_age)

        return conditions

    @staticmethod
    async def create_patient(
        db: AsyncSession,
        *,
        name: str,
        age: int,
        gender,
        phone: str,
    ) -> Patients:
        patient = Patients(
            name=name,
            age=age,
            gender=gender,
            phone=phone,
        )
        db.add(patient)
        await db.flush()
        await db.refresh(patient)
        return patient

    @staticmethod
    async def get_patient_by_id(
        db: AsyncSession,
        patient_id: int,
    ) -> Patients | None:
        result = await db.execute(
            select(Patients).where(Patients.id == patient_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def count_patients(
        cls,
        db: AsyncSession,
        *,
        name: str | None,
        gender: Gender | None,
        min_age: int | None,
        max_age: int | None,
    ) -> int:
        conditions = cls._build_conditions(
            name=name,
            gender=gender,
            min_age=min_age,
            max_age=max_age,
        )
        result = await db.execute(
            select(func.count(Patients.id)).where(*conditions)
        )
        return result.scalar_one()

    @classmethod
    async def get_patients(
        cls,
        db: AsyncSession,
        *,
        name: str | None,
        gender: Gender | None,
        min_age: int | None,
        max_age: int | None,
        offset: int,
        limit: int,
    ) -> list[Patients]:
        conditions = cls._build_conditions(
            name=name,
            gender=gender,
            min_age=min_age,
            max_age=max_age,
        )
        result = await db.execute(
            select(Patients)
            .where(*conditions)
            .order_by(Patients.created_at.desc(), Patients.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
