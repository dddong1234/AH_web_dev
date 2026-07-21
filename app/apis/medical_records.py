from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.dependencies import get_patient_or_404, require_medical_staff_or_admin
from app.core.db.databases import async_get_db
from app.models.patients import Patients
from app.models.users import User
from app.schemas.common import ErrorResponse
from app.schemas.medical_record import MedicalRecordCreateData, MedicalRecordResponse
from app.services.medical_record_service import MedicalRecordService

router = APIRouter(prefix="/api/v1/patients", tags=["Medical Records"])


ERROR_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": "AUTHENTICATION_REQUIRED (로그인 필요)",
    },
    403: {
        "model": ErrorResponse,
        "description": "PERMISSION_DENIED (접근 권한 없음)",
    },
    404: {
        "model": ErrorResponse,
        "description": "PATIENT_NOT_FOUND (환자를 찾을 수 없음)",
    },
    409: {
        "model": ErrorResponse,
        "description": "DUPLICATE_CHART_NUMBER (차트 번호 중복)",
    },
    422: {
        "model": ErrorResponse,
        "description": "INVALID_XRAY_FILE / XRAY_FILE_TOO_LARGE / VALIDATION_ERROR (파일 검증 및 입력 데이터 유효성 검증 실패)",
    },
    504: {
        "model": ErrorResponse,
        "description": "REQUEST_TIMEOUT (요청 시간 3초 초과)",
    },
}


@router.post(
    "/{patient_id}/medical-records",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="진료기록 및 X-Ray 이미지 등록 (REQ-MDR-001)",
    responses=ERROR_RESPONSES,
)
async def create_medical_record(
    patient: Patients = Depends(get_patient_or_404),
    chart_number: str = Form(..., description="진료 차트 넘버 (1~50자, Unique)"),
    symptoms: str = Form(..., description="진료 증상 (1~5000자)"),
    xray: UploadFile = File(..., description="흉부 X-Ray 이미지 파일 (jpg, jpeg, png, 최대 10MB)"),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_medical_staff_or_admin),
):
    # Pydantic 스키마 검증(공백 제거 strip_whitespace=True, 길이 제약 min/max_length) 적용
    MedicalRecordCreateData(chart_number=chart_number, symptoms=symptoms)

    return await MedicalRecordService.create_medical_record(
        db=db,
        patient_id=patient.id,
        chart_number=chart_number,
        symptoms=symptoms,
        xray_file=xray,
        current_user=current_user,
    )
