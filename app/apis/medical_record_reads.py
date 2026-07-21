from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.dependencies import (
    get_medical_record_or_404,
    get_patient_or_404,
    require_staff_or_admin,
)
from app.core.db.databases import async_get_db
from app.models.medical_records import MedicalRecord
from app.models.patients import Patients
from app.models.users import User
from app.schemas.common import ErrorResponse
from app.schemas.medical_record import (
    MedicalRecordDetailResponse,
    MedicalRecordListResponse,
)
from app.services.medical_record_read_service import MedicalRecordReadService


router = APIRouter(
    prefix="/api/v1/patients",
    tags=["Medical Records"],
)

DbSession = Annotated[AsyncSession, Depends(async_get_db)]
CurrentStaffUser = Annotated[User, Depends(require_staff_or_admin)]
CurrentPatient = Annotated[Patients, Depends(get_patient_or_404)]
CurrentMedicalRecord = Annotated[
    MedicalRecord,
    Depends(get_medical_record_or_404),
]


ERROR_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": "인증 실패",
    },
    403: {
        "model": ErrorResponse,
        "description": "권한 부족",
    },
    404: {
        "model": ErrorResponse,
        "description": "환자 또는 진료기록 없음",
    },
    422: {
        "model": ErrorResponse,
        "description": "요청값 검증 실패",
    },
    500: {
        "model": ErrorResponse,
        "description": "서버 내부 오류",
    },
}


@router.get(
    "/{patient_id}/medical-records",
    status_code=status.HTTP_200_OK,
    summary="진료기록 목록 조회 API",
    response_model=MedicalRecordListResponse,
    responses=ERROR_RESPONSES,
)
async def get_medical_records(
    patient_id: Annotated[int, Path(ge=1, description="조회 대상 환자 ID")],
    db: DbSession,
    _current_user: CurrentStaffUser,
    _patient: CurrentPatient,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> MedicalRecordListResponse:
    return await MedicalRecordReadService.get_medical_records(
        db=db,
        patient_id=patient_id,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{patient_id}/medical-records/{record_id}",
    status_code=status.HTTP_200_OK,
    summary="진료기록 상세 조회 API",
    response_model=MedicalRecordDetailResponse,
    responses=ERROR_RESPONSES,
)
async def get_medical_record_detail(
    patient_id: Annotated[int, Path(ge=1, description="조회 대상 환자 ID")],
    record_id: Annotated[int, Path(ge=1, description="조회 대상 진료기록 ID")],
    _current_user: CurrentStaffUser,
    _patient: CurrentPatient,
    record: CurrentMedicalRecord,
) -> MedicalRecordDetailResponse:
    return MedicalRecordReadService.get_medical_record_detail(record)
