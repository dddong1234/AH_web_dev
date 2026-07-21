from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from app.models.enums import Gender
from app.schemas.common import OffsetLimitPage
from app.utils.validators import normalize_phone


NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class PatientBase(BaseModel):
    name: NameStr
    age: int = Field(ge=0, le=150)
    gender: Gender
    phone: str

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("전화번호는 문자열이어야 합니다.")
        return normalize_phone(value)


class PatientCreateRequest(PatientBase):
    model_config = ConfigDict(extra="forbid")


class PatientUpdateRequest(BaseModel):
    name: NameStr | None = None
    phone: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("전화번호는 문자열이어야 합니다.")
        return normalize_phone(value)

    @model_validator(mode="after")
    def ensure_at_least_one_field(self) -> "PatientUpdateRequest":
        if self.name is None and self.phone is None:
            raise ValueError("수정할 항목을 하나 이상 입력해야 합니다.")
        return self


class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: Gender
    phone: str
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PatientListItem(PatientResponse):
    pass


class PatientListResponse(OffsetLimitPage[PatientListItem]):
    pass
