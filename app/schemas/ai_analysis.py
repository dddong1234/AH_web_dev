from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import OffsetLimitPage


class AIAnalysisResponse(BaseModel):
    id: int
    record_id: int
    is_pneumonia: bool
    confidence: float = Field(ge=0.0, le=100.0)
    heatmap_url: str
    ai_model: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("heatmap_url", mode="before")
    @classmethod
    def build_heatmap_response_url(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        if value.startswith("/uploads/"):
            return value
        return f"/uploads/{value.lstrip('/')}"


class AIAnalysisListResponse(OffsetLimitPage[AIAnalysisResponse]):
    pass
