from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis_result import AIAnalysisResult
from app.models.xray_image import XrayImage


class AIAnalysisRepository:
    @staticmethod
    async def get_by_record_and_model(
        db: AsyncSession,
        *,
        record_id: int,
        model_name: str,
    ) -> AIAnalysisResult | None:
        result = await db.execute(
            select(AIAnalysisResult).where(
                AIAnalysisResult.record_id == record_id,
                AIAnalysisResult.ai_model == model_name,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_first_xray(
        db: AsyncSession,
        *,
        record_id: int,
    ) -> XrayImage | None:
        result = await db.execute(
            select(XrayImage)
            .where(XrayImage.record_id == record_id)
            .order_by(XrayImage.id.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        record_id: int,
        is_pneumonia: bool,
        confidence: Decimal,
        heatmap_path: str,
        model_name: str,
    ) -> AIAnalysisResult:
        analysis = AIAnalysisResult(
            record_id=record_id,
            is_pneumonia=is_pneumonia,
            confidence=confidence,
            heatmap_url=heatmap_path,
            ai_model=model_name,
        )
        db.add(analysis)
        await db.flush()
        return analysis

    @staticmethod
    async def count_by_record(
        db: AsyncSession,
        *,
        record_id: int,
    ) -> int:
        result = await db.execute(
            select(func.count(AIAnalysisResult.id)).where(
                AIAnalysisResult.record_id == record_id
            )
        )
        return result.scalar_one()

    @staticmethod
    async def get_list_by_record(
        db: AsyncSession,
        *,
        record_id: int,
        offset: int,
        limit: int,
    ) -> list[AIAnalysisResult]:
        result = await db.execute(
            select(AIAnalysisResult)
            .where(AIAnalysisResult.record_id == record_id)
            .order_by(
                AIAnalysisResult.created_at.desc(),
                AIAnalysisResult.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
