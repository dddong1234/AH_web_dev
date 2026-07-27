"""Shared Redis queue/pubsub contract for Stage 3 AI analysis."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal
from uuid import uuid4


AI_MODEL_NAME = "v8-lite-densenet121-fp16"
AI_ANALYSIS_QUEUE_KEY = "ai-analysis:queue"
AI_ANALYSIS_RESULT_CHANNEL_PREFIX = "ai-analysis:result"

TaskStatus = Literal["queued", "running", "succeeded", "failed"]


def new_job_id() -> str:
    return str(uuid4())


def build_result_channel(job_id: str) -> str:
    return f"{AI_ANALYSIS_RESULT_CHANNEL_PREFIX}:{job_id}"


@dataclass(slots=True)
class AIAnalysisTaskMessage:
    job_id: str
    record_id: int
    model_name: str
    image_path: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def from_json(cls, raw: str | bytes) -> "AIAnalysisTaskMessage":
        data = _load_json_object(raw)
        return cls(
            job_id=str(data["job_id"]),
            record_id=int(data["record_id"]),
            model_name=str(data["model_name"]),
            image_path=str(data["image_path"]),
        )


@dataclass(slots=True)
class AIAnalysisResultMessage:
    job_id: str
    record_id: int
    model_name: str
    status: TaskStatus
    is_pneumonia: bool | None = None
    confidence: float | None = None
    heatmap_path: str | None = None
    error: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def from_json(cls, raw: str | bytes) -> "AIAnalysisResultMessage":
        data = _load_json_object(raw)
        return cls(
            job_id=str(data["job_id"]),
            record_id=int(data["record_id"]),
            model_name=str(data["model_name"]),
            status=_parse_status(data["status"]),
            is_pneumonia=_optional_bool(data.get("is_pneumonia")),
            confidence=_optional_float(data.get("confidence")),
            heatmap_path=_optional_str(data.get("heatmap_path")),
            error=_optional_str(data.get("error")),
        )

    def is_done(self) -> bool:
        return self.status in {"succeeded", "failed"}


def make_task_message(
    *,
    record_id: int,
    image_path: str,
    model_name: str = AI_MODEL_NAME,
    job_id: str | None = None,
) -> AIAnalysisTaskMessage:
    return AIAnalysisTaskMessage(
        job_id=job_id or new_job_id(),
        record_id=record_id,
        model_name=model_name,
        image_path=image_path,
    )


def make_running_result(task: AIAnalysisTaskMessage) -> AIAnalysisResultMessage:
    return AIAnalysisResultMessage(
        job_id=task.job_id,
        record_id=task.record_id,
        model_name=task.model_name,
        status="running",
    )


def make_success_result(
    task: AIAnalysisTaskMessage,
    *,
    is_pneumonia: bool,
    confidence: float,
    heatmap_path: str,
) -> AIAnalysisResultMessage:
    return AIAnalysisResultMessage(
        job_id=task.job_id,
        record_id=task.record_id,
        model_name=task.model_name,
        status="succeeded",
        is_pneumonia=is_pneumonia,
        confidence=float(confidence),
        heatmap_path=heatmap_path,
    )


def make_failed_result(
    task: AIAnalysisTaskMessage,
    *,
    error: str,
) -> AIAnalysisResultMessage:
    return AIAnalysisResultMessage(
        job_id=task.job_id,
        record_id=task.record_id,
        model_name=task.model_name,
        status="failed",
        error=error,
    )


def _load_json_object(raw: str | bytes) -> dict[str, Any]:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")

    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Message payload must be a JSON object.")
    return data


def _parse_status(value: Any) -> TaskStatus:
    if value not in {"queued", "running", "succeeded", "failed"}:
        raise ValueError(f"Unsupported task status: {value!r}")
    return value


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    raise ValueError("Expected bool or null.")


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("Expected float or null.")
    if isinstance(value, (int, float)):
        return float(value)
    raise ValueError("Expected float or null.")


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    raise ValueError("Expected str or null.")
