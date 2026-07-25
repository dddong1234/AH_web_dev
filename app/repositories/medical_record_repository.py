from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_records import MedicalRecord
from app.models.xray_image import XrayImage


class MedicalRecordRepository:
    @staticmethod
    async def get_by_chart_number(
        db: AsyncSession, chart_number: str
    ) -> MedicalRecord | None:
        stmt = select(MedicalRecord).where(MedicalRecord.chart_number == chart_number)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_medical_record_with_xray(
        db: AsyncSession,
        patient_id: int,
        chart_number: str,
        symptoms: str,
        uploader_id: int,
        image_relative_path: str,
    ) -> tuple[MedicalRecord, XrayImage]:
        record = MedicalRecord(
            patient_id=patient_id,
            chart_number=chart_number,
            symptoms=symptoms,
        )
        db.add(record)
        await db.flush()

        xray = XrayImage(
            record_id=record.id,
            uploader_id=uploader_id,
            image_url=image_relative_path,
            shooting_datetime=datetime.now(KST).replace(tzinfo=None),
        )
        db.add(xray)
        await db.flush()

        return record, xray
