from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.dependencies import get_patient_or_404, require_medical_staff_or_admin, require_staff_or_admin
from app.core.db.databases import async_get_db
from app.models.enums import Gender
from app.models.patients import Patients
from app.models.users import User
from app.schemas.common import ErrorResponse
from app.schemas.patient import PatientCreateRequest, PatientListQuery, PatientListResponse, PatientResponse
from app.services.patient_service import PatientService


router = APIRouter(
    prefix="/api/v1/patients",
    tags=["Patients"],
)

DbSession = Annotated[AsyncSession, Depends(async_get_db)]
CurrentMedicalUser = Annotated[User, Depends(require_medical_staff_or_admin)]
CurrentStaffUser = Annotated[User, Depends(require_staff_or_admin)]


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
        "description": "환자 없음",
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


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="환자 목록 조회 API",
    response_model=PatientListResponse,
    responses=ERROR_RESPONSES,
)
async def get_patients(
    db: DbSession,
    _current_user: CurrentStaffUser,
    name: Annotated[str | None, Query(max_length=50)] = None,
    gender: Gender | None = None,
    min_age: Annotated[int | None, Query(ge=0, le=150)] = None,
    max_age: Annotated[int | None, Query(ge=0, le=150)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PatientListResponse:
    query = PatientListQuery(
        name=name,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        offset=offset,
        limit=limit,
    )
    return await PatientService.get_patients(db=db, query=query)
@router.get(
    "/{patient_id}",
    status_code=status.HTTP_200_OK,
    summary="환자 상세 조회 API",
    response_model=PatientResponse,
    responses=ERROR_RESPONSES,
)
async def get_patient_detail(
    _current_user: CurrentStaffUser,
    patient: Annotated[Patients, Depends(get_patient_or_404)],
    patient_id: Annotated[int, Path(ge=1, description="조회 대상 환자 ID")],
) -> PatientResponse:
    return PatientResponse.model_validate(patient)
