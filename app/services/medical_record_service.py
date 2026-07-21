from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.exceptions import DuplicateChartNumberError
from app.models.users import User
from app.repositories.medical_record_repository import MedicalRecordRepository
from app.schemas.medical_record import MedicalRecordResponse
from app.services.file_storage import delete_xray_file, save_xray_file
from app.utils.validators import build_xray_url


class MedicalRecordService:
    @staticmethod
    async def create_medical_record(
        db: AsyncSession,
        patient_id: int,
        chart_number: str,
        symptoms: str,
        xray_file: UploadFile,
        current_user: User,
    ) -> MedicalRecordResponse:
        chart_number_cleaned = chart_number.strip()
        existing = await MedicalRecordRepository.get_by_chart_number(
            db, chart_number_cleaned
        )
        if existing:
            raise DuplicateChartNumberError()

        relative_path = await save_xray_file(
            patient_id=patient_id, upload_file=xray_file
        )

        try:
            record, _xray = (
                await MedicalRecordRepository.create_medical_record_with_xray(
                    db=db,
                    patient_id=patient_id,
                    chart_number=chart_number_cleaned,
                    symptoms=symptoms.strip(),
                    uploader_id=current_user.id,
                    image_relative_path=relative_path,
                )
            )
            await db.commit()
            await db.refresh(record)
        except Exception:
            await db.rollback()
            delete_xray_file(relative_path)
            raise

        return MedicalRecordResponse(
            id=record.id,
            patient_id=record.patient_id,
            chart_number=record.chart_number,
            symptoms=record.symptoms,
            xray_url=build_xray_url(relative_path),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
