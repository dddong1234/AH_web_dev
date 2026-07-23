import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.dependencies import (
    get_medical_record_or_404,
    get_patient_or_404,
    require_staff_or_admin,
)
from app.core.auth.exceptions import RequestTimeoutError
from app.core.db.databases import async_get_db
from app.models.medical_records import MedicalRecord
from app.models.patients import Patients
from app.models.users import User
from app.schemas.ai_analysis import (
    AIAnalysisListResponse,
    AIAnalysisResponse,
)
from app.schemas.common import ErrorResponse
from app.services.ai_analysis_service import AIAnalysisService


router = APIRouter(
    prefix="/api/v1/patients",
    tags=["AI Analyses"],
)

AI_MODEL_NAME = "v8-lite-densenet121-fp16"

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
        "description": "요청값 검증 실패 또는 X-ray 없음",
    },
    500: {
        "model": ErrorResponse,
        "description": "AI 추론, Grad-CAM 생성 또는 저장 실패",
    },
    504: {
        "model": ErrorResponse,
        "description": "요청 처리 시간 초과",
    },
}


@router.post(
    "/{patient_id}/medical-records/{record_id}/ai-analyses",
    status_code=status.HTTP_200_OK,
    summary="폐렴 예측 실행 또는 기존 결과 반환 API",
    response_model=AIAnalysisResponse,
    responses=ERROR_RESPONSES,
)
async def get_or_create_ai_analysis(
    patient_id: Annotated[int, Path(ge=1, description="대상 환자 ID")],
    record_id: Annotated[int, Path(ge=1, description="대상 진료기록 ID")],
    db: DbSession,
    _current_user: CurrentStaffUser,
    _patient: CurrentPatient,
    _record: CurrentMedicalRecord,
) -> AIAnalysisResponse:
    try:
        result = await asyncio.wait_for(
            AIAnalysisService.get_or_create_ai_analysis(
                db=db,
                record_id=record_id,
                model_name=AI_MODEL_NAME,
            ),
            timeout=3.0,
        )
    except TimeoutError as exc:
        raise RequestTimeoutError() from exc

    return AIAnalysisResponse.model_validate(result)


@router.get(
    "/{patient_id}/medical-records/{record_id}/ai-analyses",
    status_code=status.HTTP_200_OK,
    summary="폐렴 예측 결과 목록 조회 API",
    response_model=AIAnalysisListResponse,
    responses=ERROR_RESPONSES,
)
async def get_ai_analyses(
    patient_id: Annotated[int, Path(ge=1, description="대상 환자 ID")],
    record_id: Annotated[int, Path(ge=1, description="대상 진료기록 ID")],
    db: DbSession,
    _current_user: CurrentStaffUser,
    _patient: CurrentPatient,
    _record: CurrentMedicalRecord,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AIAnalysisListResponse:
    return await AIAnalysisService.get_ai_analyses(
        db=db,
        record_id=record_id,
        offset=offset,
        limit=limit,
    )
