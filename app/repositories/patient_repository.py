from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patients import Patients


class PatientRepository:
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
