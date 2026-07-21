from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class DataResponse(BaseModel, Generic[T]):
    data: T


class ErrorResponse(BaseModel):
    code: str
    message: str


class EmptyData(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OffsetLimitParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)

    model_config = ConfigDict(extra="forbid")


class OffsetLimitPage(BaseModel, Generic[T]):
    items: list[T]
    total: int
    offset: int
    limit: int
