import asyncio
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.exceptions import (
    AIInferenceFailedError,
    AppBaseException,
    HeatmapStorageFailedError,
    XrayImageNotFoundError,
)
from app.repositories.ai_analysis_repository import AIAnalysisRepository
from app.schemas.ai_analysis import (
    AIAnalysisListResponse,
    AIAnalysisResponse,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_ROOT = PROJECT_ROOT / "uploads"


def _delete_heatmap_file(relative_path: str) -> None:
    target = (UPLOAD_ROOT / relative_path).resolve()
    heatmap_root = (UPLOAD_ROOT / "heatmaps").resolve()

    if heatmap_root not in target.parents:
        return

    try:
        if target.is_file():
            target.unlink()
    except OSError:
        return

    parent = target.parent
    try:
        if parent != heatmap_root and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
    except OSError:
        return


def _get_predict_pneumonia():
    try:
        from worker.model import predict_pneumonia
    except (ImportError, OSError, RuntimeError) as exc:
        raise AIInferenceFailedError() from exc
    return predict_pneumonia


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
        except SQLAlchemyError as exc:
            raise AppBaseException() from exc

        if existing is not None:
            return AIAnalysisResponse.model_validate(existing)

        try:
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

        predict_pneumonia = _get_predict_pneumonia()
        try:
            result: dict[str, Any] = await asyncio.to_thread(
                predict_pneumonia,
                image_path,
                record_id,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise AIInferenceFailedError() from exc

        is_pneumonia = result.get("is_pneumonia")
        confidence = result.get("confidence")
        heatmap_path = result.get("heatmap_path")

        if not isinstance(heatmap_path, str) or not heatmap_path:
            raise HeatmapStorageFailedError()

        heatmap_root = (UPLOAD_ROOT / "heatmaps" / str(record_id)).resolve()
        saved_heatmap = (UPLOAD_ROOT / heatmap_path).resolve()
        if saved_heatmap.parent != heatmap_root or saved_heatmap.suffix.lower() != ".png":
            raise HeatmapStorageFailedError()

        if not saved_heatmap.is_file():
            raise HeatmapStorageFailedError()

        if not isinstance(is_pneumonia, bool):
            _delete_heatmap_file(heatmap_path)
            raise AIInferenceFailedError()
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            _delete_heatmap_file(heatmap_path)
            raise AIInferenceFailedError()
        if not 0.0 <= float(confidence) <= 1.0:
            _delete_heatmap_file(heatmap_path)
            raise AIInferenceFailedError()

        confidence_percent = Decimal(str(float(confidence) * 100)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        try:
            analysis = await AIAnalysisRepository.create(
                db=db,
                record_id=record_id,
                is_pneumonia=is_pneumonia,
                confidence=confidence_percent,
                heatmap_path=heatmap_path,
                model_name=model_name,
            )
            await db.commit()
            await db.refresh(analysis)
        except IntegrityError:
            await db.rollback()
            _delete_heatmap_file(heatmap_path)
            existing = await AIAnalysisRepository.get_by_record_and_model(
                db=db,
                record_id=record_id,
                model_name=model_name,
            )
            if existing is None:
                raise AppBaseException()
            return AIAnalysisResponse.model_validate(existing)
        except SQLAlchemyError as exc:
            await db.rollback()
            _delete_heatmap_file(heatmap_path)
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
