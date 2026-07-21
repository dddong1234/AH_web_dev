from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.dependencies import (
    get_patient_or_404,
    require_staff_or_admin,
)
from app.core.db.databases import async_get_db
from app.models.patients import Patients
from app.models.users import User
from app.schemas.common import ErrorResponse
from app.schemas.patient import PatientResponse, PatientUpdateRequest
from app.services.patient_edit_delete_service import (
    PatientEditDeleteService,
)


router = APIRouter(
    prefix="/api/v1/patients",
    tags=["Patients"],
)

DbSession = Annotated[AsyncSession, Depends(async_get_db)]
CurrentStaffOrAdmin = Annotated[
    User,
    Depends(require_staff_or_admin),
]
CurrentPatient = Annotated[
    Patients,
    Depends(get_patient_or_404),
]


ERROR_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": "인증 실패",
    },
    403: {
        "model": ErrorResponse,
        "description": "접근 권한 없음",
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


@router.patch(
    "/{patient_id}",
    summary="환자 정보 수정 API",
    response_model=PatientResponse,
    responses=ERROR_RESPONSES,
)
async def update_patient(
    request: PatientUpdateRequest,
    db: DbSession,
    _current_user: CurrentStaffOrAdmin,
    patient: CurrentPatient,
    patient_id: Annotated[int, Path(ge=1, description="환자 ID")],
) -> PatientResponse:
    return await PatientEditDeleteService.update_patient(
        db=db,
        patient=patient,
        request=request,
    )


@router.delete(
    "/{patient_id}",
    summary="환자 정보 삭제 API",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=ERROR_RESPONSES,
)
async def delete_patient(
    db: DbSession,
    _current_user: CurrentStaffOrAdmin,
    patient: CurrentPatient,
    patient_id: Annotated[int, Path(ge=1, description="환자 ID")],
) -> Response:
    await PatientEditDeleteService.delete_patient(
        db=db,
        patient=patient,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)