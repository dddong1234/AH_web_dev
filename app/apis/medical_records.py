from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.dependencies import get_patient_or_404, require_medical_staff_or_admin
from app.core.db.databases import async_get_db
from app.models.patients import Patients
from app.models.users import User
from app.schemas.medical_record import MedicalRecordResponse
from app.services.medical_record_service import MedicalRecordService

router = APIRouter(prefix="/api/v1/patients", tags=["Medical Records"])


@router.post(
    "/{patient_id}/medical-records",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="진료기록 및 X-Ray 이미지 등록 (REQ-MDR-001)",
)
async def create_medical_record(
    patient: Patients = Depends(get_patient_or_404),
    chart_number: str = Form(..., description="진료 차트 넘버 (1~50자, Unique)"),
    symptoms: str = Form(..., description="진료 증상 (1~5000자)"),
    xray: UploadFile = File(..., description="흉부 X-Ray 이미지 파일 (jpg, jpeg, png, 최대 10MB)"),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_medical_staff_or_admin),
):
    return await MedicalRecordService.create_medical_record(
        db=db,
        patient_id=patient.id,
        chart_number=chart_number,
        symptoms=symptoms,
        xray_file=xray,
        current_user=current_user,
    )
