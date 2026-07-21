from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.dependencies import require_medical_staff_or_admin
from app.core.db.databases import async_get_db
from app.models.users import User
from app.schemas.common import ErrorResponse
from app.schemas.patient import PatientCreateRequest, PatientResponse
from app.services.patient_service import PatientService


router = APIRouter(
    prefix="/api/v1/patients",
    tags=["Patients"],
)

DbSession = Annotated[AsyncSession, Depends(async_get_db)]
CurrentMedicalUser = Annotated[User, Depends(require_medical_staff_or_admin)]


ERROR_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": "인증 실패",
    },
    403: {
        "model": ErrorResponse,
        "description": "권한 부족",
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


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="환자 정보 등록 API",
    response_model=PatientResponse,
    responses=ERROR_RESPONSES,
)
async def create_patient(
    request: PatientCreateRequest,
    db: DbSession,
    _current_user: CurrentMedicalUser,
) -> PatientResponse:
    patient = await PatientService.create_patient(db=db, request=request)
    return PatientResponse.model_validate(patient)
