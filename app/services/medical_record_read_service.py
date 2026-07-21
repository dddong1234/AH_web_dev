from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.exceptions import AppBaseException
from app.models.medical_records import MedicalRecord
from app.repositories.medical_record_read_repository import MedicalRecordReadRepository
from app.schemas.medical_record import (
    MedicalRecordDetailResponse,
    MedicalRecordListItem,
    MedicalRecordListResponse,
)


class MedicalRecordReadService:
    @staticmethod
    async def get_medical_records(
        db: AsyncSession,
        *,
        patient_id: int,
        offset: int,
        limit: int,
    ) -> MedicalRecordListResponse:
        try:
            total = await MedicalRecordReadRepository.count_by_patient(
                db=db,
                patient_id=patient_id,
            )
            records = await MedicalRecordReadRepository.get_list_by_patient(
                db=db,
                patient_id=patient_id,
                offset=offset,
                limit=limit,
            )
        except SQLAlchemyError as exc:
            raise AppBaseException() from exc

        return MedicalRecordListResponse(
            items=[
                MedicalRecordListItem.model_validate(record)
                for record in records
            ],
            total=total,
            offset=offset,
            limit=limit,
        )

    @staticmethod
    def get_medical_record_detail(
        record: MedicalRecord,
    ) -> MedicalRecordDetailResponse:
        # Stage 5 계약에서는 진료기록 등록 시 X-Ray 이미지를 1개만 받는다.
        # DB 관계는 1:N이므로 가장 먼저 생성된 이미지를 응답에 사용한다.
        xray_image = min(
            record.xray_images,
            key=lambda image: image.id,
            default=None,
        )
        if xray_image is None:
            raise AppBaseException(message="X-Ray image not found")

        return MedicalRecordDetailResponse.from_record(
            record_id=record.id,
            patient_id=record.patient_id,
            chart_number=record.chart_number,
            symptoms=record.symptoms,
            image_path=xray_image.image_url,
            created_at=record.created_at,
        )
