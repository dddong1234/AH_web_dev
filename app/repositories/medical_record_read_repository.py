from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_records import MedicalRecord


class MedicalRecordReadRepository:
    @staticmethod
    async def count_by_patient(
        db: AsyncSession,
        *,
        patient_id: int,
    ) -> int:
        result = await db.execute(
            select(func.count(MedicalRecord.id)).where(
                MedicalRecord.patient_id == patient_id
            )
        )
        return result.scalar_one()

    @staticmethod
    async def get_list_by_patient(
        db: AsyncSession,
        *,
        patient_id: int,
        offset: int,
        limit: int,
    ) -> list[MedicalRecord]:
        result = await db.execute(
            select(MedicalRecord)
            .where(MedicalRecord.patient_id == patient_id)
            .order_by(
                MedicalRecord.created_at.desc(),
                MedicalRecord.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
