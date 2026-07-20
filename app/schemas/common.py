from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


class DataResponse(BaseModel, Generic[T]):
    data: T


class ErrorResponse(BaseModel):
    code: str
    message: str


class EmptyData(BaseModel):
    model_config = ConfigDict(extra="forbid")
