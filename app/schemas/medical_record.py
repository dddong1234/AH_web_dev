from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.schemas.common import OffsetLimitPage
from app.utils.validators import build_xray_url, truncate_symptoms


ChartNumberStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
SymptomsStr = Annotated[str, StringConstraints(min_length=1, max_length=5000)]


class MedicalRecordCreateData(BaseModel):
    chart_number: ChartNumberStr
    symptoms: SymptomsStr

    model_config = ConfigDict(extra="forbid")


class MedicalRecordResponse(BaseModel):
    id: int
    patient_id: int
    chart_number: str
    symptoms: str
    xray_url: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class MedicalRecordListItem(BaseModel):
    id: int
    chart_number: str
    symptoms: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("symptoms", mode="before")
    @classmethod
    def shorten_symptoms(cls, value: object) -> object:
        if isinstance(value, str):
            return truncate_symptoms(value)
        return value


class MedicalRecordListResponse(OffsetLimitPage[MedicalRecordListItem]):
    pass


class MedicalRecordDetailResponse(BaseModel):
    id: int
    patient_id: int
    chart_number: str
    symptoms: str
    xray_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_record(
        cls,
        record_id: int,
        patient_id: int,
        chart_number: str,
        symptoms: str,
        image_path: str,
        created_at: datetime,
    ) -> "MedicalRecordDetailResponse":
        return cls(
            id=record_id,
            patient_id=patient_id,
            chart_number=chart_number,
            symptoms=symptoms,
            xray_url=build_xray_url(image_path),
            created_at=created_at,
        )
