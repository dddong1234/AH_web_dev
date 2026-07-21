from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.exceptions import AppBaseException
from app.models.patients import Patients
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import PatientCreateRequest, PatientListItem, PatientListQuery, PatientListResponse


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

    @staticmethod
    async def get_patients(
        db: AsyncSession,
        query: PatientListQuery,
    ) -> PatientListResponse:
        try:
            total = await PatientRepository.count_patients(
                db=db,
                name=query.name,
                gender=query.gender,
                min_age=query.min_age,
                max_age=query.max_age,
            )
            patients = await PatientRepository.get_patients(
                db=db,
                name=query.name,
                gender=query.gender,
                min_age=query.min_age,
                max_age=query.max_age,
                offset=query.offset,
                limit=query.limit,
            )
        except SQLAlchemyError as exc:
            raise AppBaseException() from exc

        return PatientListResponse(
            items=[PatientListItem.model_validate(patient) for patient in patients],
            total=total,
            offset=query.offset,
            limit=query.limit,
        )
