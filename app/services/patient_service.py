from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.exceptions import AppBaseException
from app.models.patients import Patients
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import PatientCreateRequest


class PatientService:
    @staticmethod
    async def create_patient(
        db: AsyncSession,
        request: PatientCreateRequest,
    ) -> Patients:
        try:
            patient = await PatientRepository.create_patient(
                db=db,
                name=request.name,
                age=request.age,
                gender=request.gender,
                phone=request.phone,
            )
            await db.commit()
            return patient
        except SQLAlchemyError as exc:
            await db.rollback()
            raise AppBaseException() from exc
