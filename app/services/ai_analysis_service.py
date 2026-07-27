from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.exceptions import (
    AIInferenceFailedError,
    AIQueueUnavailableError,
    AppBaseException,
    HeatmapStorageFailedError,
    RequestTimeoutError,
    XrayImageNotFoundError,
)
from app.core.config import settings
from app.core.redis_client import (
    AIAnalysisResultTimeoutError,
    RedisClientError,
    enqueue_and_wait_for_result,
)
from app.repositories.ai_analysis_repository import AIAnalysisRepository
from app.schemas.ai_analysis import AIAnalysisListResponse, AIAnalysisResponse
from shared.ai_queue_protocol import AIAnalysisResultMessage, make_task_message


PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_ROOT = PROJECT_ROOT / "uploads"


def _validate_success_result(
    result: AIAnalysisResultMessage,
    *,
    record_id: int,
    model_name: str,
) -> tuple[bool, Decimal, str]:
    if result.record_id != record_id or result.model_name != model_name:
        raise AIInferenceFailedError("AI worker returned a mismatched result.")
    if result.status == "failed":
        raise AIInferenceFailedError(result.error or "AI worker inference failed.")
    if result.status != "succeeded":
        raise AIInferenceFailedError("AI worker returned an invalid final status.")

    if not isinstance(result.is_pneumonia, bool):
        raise AIInferenceFailedError("AI worker returned an invalid prediction.")
    if result.confidence is None or not 0.0 <= result.confidence <= 1.0:
        raise AIInferenceFailedError("AI worker returned an invalid confidence.")
    if not result.heatmap_path:
        raise HeatmapStorageFailedError()

    heatmap_root = (UPLOAD_ROOT / "heatmaps" / str(record_id)).resolve()
    saved_heatmap = (UPLOAD_ROOT / result.heatmap_path).resolve()
    if (
        saved_heatmap.parent != heatmap_root
        or saved_heatmap.suffix.lower() != ".png"
        or not saved_heatmap.is_file()
    ):
        raise HeatmapStorageFailedError()

    confidence_percent = Decimal(str(result.confidence * 100)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return result.is_pneumonia, confidence_percent, result.heatmap_path


class AIAnalysisService:
    @staticmethod
    async def get_or_create_ai_analysis(
        db: AsyncSession,
        *,
        record_id: int,
        model_name: str,
    ) -> AIAnalysisResponse:
        try:
            existing = await AIAnalysisRepository.get_by_record_and_model(
                db=db,
                record_id=record_id,
                model_name=model_name,
            )
            if existing is not None:
                return AIAnalysisResponse.model_validate(existing)

            xray = await AIAnalysisRepository.get_first_xray(
                db=db,
                record_id=record_id,
            )
        except SQLAlchemyError as exc:
            raise AppBaseException() from exc

        if xray is None:
            raise XrayImageNotFoundError()

        image_path = UPLOAD_ROOT / xray.image_url
        if not image_path.is_file():
            raise XrayImageNotFoundError()

        task = make_task_message(
            record_id=record_id,
            model_name=model_name,
            image_path=str(xray.image_url),
        )
        try:
            result = await enqueue_and_wait_for_result(
                task,
                timeout_seconds=settings.AI_ANALYSIS_TIMEOUT_SECONDS,
            )
        except AIAnalysisResultTimeoutError as exc:
            raise RequestTimeoutError() from exc
        except RedisClientError as exc:
            raise AIQueueUnavailableError() from exc

        is_pneumonia, confidence, heatmap_path = _validate_success_result(
            result,
            record_id=record_id,
            model_name=model_name,
        )

        try:
            analysis = await AIAnalysisRepository.create(
                db=db,
                record_id=record_id,
                is_pneumonia=is_pneumonia,
                confidence=confidence,
                heatmap_path=heatmap_path,
                model_name=model_name,
            )
            await db.commit()
            await db.refresh(analysis)
        except IntegrityError:
            await db.rollback()
            try:
                existing = await AIAnalysisRepository.get_by_record_and_model(
                    db=db,
                    record_id=record_id,
                    model_name=model_name,
                )
            except SQLAlchemyError as exc:
                raise AppBaseException() from exc
            if existing is None:
                raise AppBaseException()
            return AIAnalysisResponse.model_validate(existing)
        except SQLAlchemyError as exc:
            await db.rollback()
            raise AppBaseException() from exc

        return AIAnalysisResponse.model_validate(analysis)

    @staticmethod
    async def get_ai_analyses(
        db: AsyncSession,
        *,
        record_id: int,
        offset: int,
        limit: int,
    ) -> AIAnalysisListResponse:
        try:
            total = await AIAnalysisRepository.count_by_record(
                db=db,
                record_id=record_id,
            )
            analyses = await AIAnalysisRepository.get_list_by_record(
                db=db,
                record_id=record_id,
                offset=offset,
                limit=limit,
            )
        except SQLAlchemyError as exc:
            raise AppBaseException() from exc

        return AIAnalysisListResponse(
            items=[
                AIAnalysisResponse.model_validate(analysis)
                for analysis in analyses
            ],
            total=total,
            offset=offset,
            limit=limit,
        )
