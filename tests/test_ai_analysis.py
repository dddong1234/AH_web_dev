import tempfile
import unittest
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.auth.exceptions import AppBaseException, XrayImageNotFoundError
from app.repositories.ai_analysis_repository import AIAnalysisRepository
from app.schemas.ai_analysis import AIAnalysisResponse
from app.services import ai_analysis_service as service_module
from app.services.ai_analysis_service import AIAnalysisService


MODEL_NAME = "v8-lite-densenet121-fp16"


def make_analysis(**overrides):
    values = {
        "id": 1,
        "record_id": 10,
        "is_pneumonia": True,
        "confidence": Decimal("94.50"),
        "heatmap_url": "heatmaps/10/test.png",
        "ai_model": MODEL_NAME,
        "created_at": datetime.now(UTC),
        "updated_at": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class AIAnalysisSchemaTest(unittest.TestCase):
    def test_relative_heatmap_path_is_converted_to_response_url(self) -> None:
        response = AIAnalysisResponse.model_validate(make_analysis())

        self.assertEqual(
            response.heatmap_url,
            "/uploads/heatmaps/10/test.png",
        )

    def test_existing_response_url_is_not_prefixed_twice(self) -> None:
        response = AIAnalysisResponse.model_validate(
            make_analysis(heatmap_url="/uploads/heatmaps/10/test.png")
        )

        self.assertEqual(
            response.heatmap_url,
            "/uploads/heatmaps/10/test.png",
        )

    def test_confidence_must_be_between_zero_and_one_hundred(self) -> None:
        with self.assertRaises(ValidationError):
            AIAnalysisResponse.model_validate(make_analysis(confidence=100.01))


class AIAnalysisServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_existing_result_is_reused_without_loading_xray(self) -> None:
        existing = make_analysis()

        with (
            patch.object(
                AIAnalysisRepository,
                "get_by_record_and_model",
                new=AsyncMock(return_value=existing),
            ),
            patch.object(
                AIAnalysisRepository,
                "get_first_xray",
                new=AsyncMock(),
            ) as get_first_xray,
        ):
            response = await AIAnalysisService.get_or_create_ai_analysis(
                db=AsyncMock(),
                record_id=10,
                model_name=MODEL_NAME,
            )

        self.assertEqual(response.id, existing.id)
        get_first_xray.assert_not_awaited()

    async def test_missing_xray_raises_domain_error(self) -> None:
        with (
            patch.object(
                AIAnalysisRepository,
                "get_by_record_and_model",
                new=AsyncMock(return_value=None),
            ),
            patch.object(
                AIAnalysisRepository,
                "get_first_xray",
                new=AsyncMock(return_value=None),
            ),
        ):
            with self.assertRaises(XrayImageNotFoundError):
                await AIAnalysisService.get_or_create_ai_analysis(
                    db=AsyncMock(),
                    record_id=10,
                    model_name=MODEL_NAME,
                )

    async def test_new_prediction_is_converted_and_saved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_root = Path(temp_dir) / "uploads"
            xray_path = upload_root / "xrays" / "1" / "source.png"
            xray_path.parent.mkdir(parents=True)
            xray_path.write_bytes(b"xray")

            heatmap_path = "heatmaps/10/generated.png"

            def fake_predict(_image_path: Path, record_id: int):
                target = upload_root / heatmap_path
                target.parent.mkdir(parents=True)
                target.write_bytes(b"png")
                return {
                    "is_pneumonia": True,
                    "confidence": 0.945,
                    "heatmap_path": heatmap_path,
                    "heatmap_url": f"/uploads/{heatmap_path}",
                }

            captured: dict[str, object] = {}

            async def fake_create(**kwargs):
                captured.update(kwargs)
                return make_analysis(
                    confidence=kwargs["confidence"],
                    heatmap_url=kwargs["heatmap_path"],
                )

            db = AsyncMock()
            with (
                patch.object(service_module, "UPLOAD_ROOT", upload_root),
                patch.object(
                    service_module,
                    "_get_predict_pneumonia",
                    return_value=fake_predict,
                ),
                patch.object(
                    AIAnalysisRepository,
                    "get_by_record_and_model",
                    new=AsyncMock(return_value=None),
                ),
                patch.object(
                    AIAnalysisRepository,
                    "get_first_xray",
                    new=AsyncMock(
                        return_value=SimpleNamespace(
                            image_url="xrays/1/source.png"
                        )
                    ),
                ),
                patch.object(
                    AIAnalysisRepository,
                    "create",
                    new=AsyncMock(side_effect=fake_create),
                ),
            ):
                response = await AIAnalysisService.get_or_create_ai_analysis(
                    db=db,
                    record_id=10,
                    model_name=MODEL_NAME,
                )

            self.assertEqual(captured["confidence"], Decimal("94.50"))
            self.assertEqual(captured["heatmap_path"], heatmap_path)
            self.assertEqual(response.heatmap_url, f"/uploads/{heatmap_path}")
            db.commit.assert_awaited_once()

    async def test_heatmap_is_deleted_when_database_save_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_root = Path(temp_dir) / "uploads"
            xray_path = upload_root / "xrays" / "1" / "source.png"
            xray_path.parent.mkdir(parents=True)
            xray_path.write_bytes(b"xray")

            relative_heatmap = "heatmaps/10/orphan.png"
            absolute_heatmap = upload_root / relative_heatmap

            def fake_predict(_image_path: Path, record_id: int):
                absolute_heatmap.parent.mkdir(parents=True)
                absolute_heatmap.write_bytes(b"png")
                return {
                    "is_pneumonia": False,
                    "confidence": 0.9,
                    "heatmap_path": relative_heatmap,
                    "heatmap_url": f"/uploads/{relative_heatmap}",
                }

            db = AsyncMock()
            with (
                patch.object(service_module, "UPLOAD_ROOT", upload_root),
                patch.object(
                    service_module,
                    "_get_predict_pneumonia",
                    return_value=fake_predict,
                ),
                patch.object(
                    AIAnalysisRepository,
                    "get_by_record_and_model",
                    new=AsyncMock(return_value=None),
                ),
                patch.object(
                    AIAnalysisRepository,
                    "get_first_xray",
                    new=AsyncMock(
                        return_value=SimpleNamespace(
                            image_url="xrays/1/source.png"
                        )
                    ),
                ),
                patch.object(
                    AIAnalysisRepository,
                    "create",
                    new=AsyncMock(side_effect=SQLAlchemyError()),
                ),
            ):
                with self.assertRaises(AppBaseException):
                    await AIAnalysisService.get_or_create_ai_analysis(
                        db=db,
                        record_id=10,
                        model_name=MODEL_NAME,
                    )

            self.assertFalse(absolute_heatmap.exists())
            db.rollback.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
