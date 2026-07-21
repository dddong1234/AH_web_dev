from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth.dependencies import get_current_active_user
from app.core.auth.exceptions import MedicalRecordNotFoundError, PatientNotFoundError, PermissionDeniedError
from app.core.db.databases import async_get_db
from app.models.enums import Department, Role
from app.models.medical_records import MedicalRecord
from app.models.patients import Patients
from app.models.users import User


async def require_staff_or_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if current_user.role not in {Role.STAFF, Role.ADMIN}:
        raise PermissionDeniedError()
    return current_user


async def require_medical_staff_or_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if current_user.role == Role.ADMIN:
        return current_user
    if current_user.role != Role.STAFF or current_user.department != Department.MEDICAL:
        raise PermissionDeniedError()
    return current_user


async def get_patient_or_404(
    patient_id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> Patients:
    patient = await db.get(Patients, patient_id)
    if patient is None:
        raise PatientNotFoundError()
    return patient


async def get_medical_record_or_404(
    patient_id: int,
    record_id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> MedicalRecord:
    stmt = (
        select(MedicalRecord)
        .options(selectinload(MedicalRecord.xray_images))
        .where(
            MedicalRecord.id == record_id,
            MedicalRecord.patient_id == patient_id,
        )
    )
    record = await db.scalar(stmt)
    if record is None:
        raise MedicalRecordNotFoundError()
    return record
