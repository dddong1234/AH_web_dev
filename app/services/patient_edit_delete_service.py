from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.exceptions import AppBaseException
from app.models.medical_records import MedicalRecord
from app.models.patients import Patients
from app.models.xray_image import XrayImage
from app.schemas.patient import PatientResponse, PatientUpdateRequest
from app.services.file_storage import delete_xray_file


class PatientEditDeleteService:
    @staticmethod
    async def update_patient(
        db: AsyncSession,
        patient: Patients,
        request: PatientUpdateRequest,
    ) -> PatientResponse:
        try:
            # 실제 요청에 포함된 필드만 수정한다.
            update_data = request.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(patient, field, value)

            await db.commit()
            await db.refresh(patient)

        except SQLAlchemyError as exc:
            await db.rollback()
            raise AppBaseException() from exc

        return PatientResponse(
            id=patient.id,
            name=patient.name,
            age=patient.age,
            gender=patient.gender,
            phone=patient.phone,
            created_at=patient.created_at.isoformat(),
            updated_at=(
                patient.updated_at.isoformat()
                if patient.updated_at is not None
                else None
            ),
        )

    @staticmethod
    async def delete_patient(
        db: AsyncSession,
        patient: Patients,
    ) -> None:
        try:
            # DB 삭제 전에 실제 X-Ray 파일 경로를 수집한다.
            statement = (
                select(XrayImage.image_url)
                .join(
                    MedicalRecord,
                    XrayImage.record_id == MedicalRecord.id,
                )
                .where(MedicalRecord.patient_id == patient.id)
            )
            result = await db.execute(statement)
            xray_paths = list(result.scalars().all())

            # Patient → MedicalRecord → XrayImage는 cascade로 삭제된다.
            await db.delete(patient)
            await db.commit()

        except SQLAlchemyError as exc:
            await db.rollback()
            raise AppBaseException() from exc

        # DB commit 이후 실제 파일을 삭제한다.
        for relative_path in xray_paths:
            delete_xray_file(relative_path)