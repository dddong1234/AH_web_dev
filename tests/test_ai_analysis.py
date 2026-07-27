import tempfile
import unittest
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError

from app.core.auth.exceptions import (
    AIInferenceFailedError,
    AIQueueUnavailableError,
    RequestTimeoutError,
    XrayImageNotFoundError,
)
from app.core.redis_client import (
    AIAnalysisResultTimeoutError,
    RedisClientError,
)
from app.repositories.ai_analysis_repository import AIAnalysisRepository
from app.schemas.ai_analysis import AIAnalysisResponse
from app.services import ai_analysis_service as service_module
from app.services.ai_analysis_service import AIAnalysisService
from shared.ai_queue_protocol import AIAnalysisResultMessage


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


def make_result(**overrides):
    values = {
        "job_id": "job-id",
        "record_id": 10,
        "model_name": MODEL_NAME,
        "status": "succeeded",
        "is_pneumonia": True,
        "confidence": 0.945,
        "heatmap_path": "heatmaps/10/generated.png",
    }
    values.update(overrides)
    return AIAnalysisResultMessage(**values)


class AIAnalysisSchemaTest(unittest.TestCase):
    def test_relative_heatmap_path_is_converted_to_response_url(self) -> None:
        response = AIAnalysisResponse.model_validate(make_analysis())
        self.assertEqual(response.heatmap_url, "/uploads/heatmaps/10/test.png")

    def test_confidence_must_be_between_zero_and_one_hundred(self) -> None:
        with self.assertRaises(ValidationError):
            AIAnalysisResponse.model_validate(make_analysis(confidence=100.01))


class AIAnalysisServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_existing_result_is_reused_without_enqueue(self) -> None:
        existing = make_analysis()
        with (
            patch.object(
                AIAnalysisRepository,
                "get_by_record_and_model",
                new=AsyncMock(return_value=existing),
            ),
            patch.object(
                service_module,
                "enqueue_and_wait_for_result",
                new=AsyncMock(),
            ) as enqueue,
        ):
            response = await AIAnalysisService.get_or_create_ai_analysis(
                db=AsyncMock(),
                record_id=10,
                model_name=MODEL_NAME,
            )

        self.assertEqual(response.id, existing.id)
        enqueue.assert_not_awaited()

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

    async def test_worker_result_is_converted_and_saved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_root = Path(temp_dir) / "uploads"
            xray = upload_root / "xrays/1/source.png"
            heatmap = upload_root / "heatmaps/10/generated.png"
            xray.parent.mkdir(parents=True)
            heatmap.parent.mkdir(parents=True)
            xray.write_bytes(b"xray")
            heatmap.write_bytes(b"png")

            captured = {}

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
                    service_module,
                    "enqueue_and_wait_for_result",
                    new=AsyncMock(return_value=make_result()),
                ) as enqueue,
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

            task = enqueue.await_args.args[0]
            self.assertEqual(task.image_path, "xrays/1/source.png")
            self.assertEqual(captured["confidence"], Decimal("94.50"))
            self.assertEqual(response.heatmap_url, "/uploads/heatmaps/10/generated.png")
            db.commit.assert_awaited_once()

    async def test_failed_worker_result_becomes_inference_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_root = Path(temp_dir) / "uploads"
            xray = upload_root / "xrays/1/source.png"
            xray.parent.mkdir(parents=True)
            xray.write_bytes(b"xray")

            with (
                patch.object(service_module, "UPLOAD_ROOT", upload_root),
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
                    service_module,
                    "enqueue_and_wait_for_result",
                    new=AsyncMock(
                        return_value=make_result(
                            status="failed",
                            is_pneumonia=None,
                            confidence=None,
                            heatmap_path=None,
                            error="model crashed",
                        )
                    ),
                ),
            ):
                with self.assertRaises(AIInferenceFailedError):
                    await AIAnalysisService.get_or_create_ai_analysis(
                        db=AsyncMock(),
                        record_id=10,
                        model_name=MODEL_NAME,
                    )

    async def test_queue_timeout_and_connection_error_are_mapped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_root = Path(temp_dir) / "uploads"
            xray = upload_root / "xrays/1/source.png"
            xray.parent.mkdir(parents=True)
            xray.write_bytes(b"xray")
            common_patches = (
                patch.object(service_module, "UPLOAD_ROOT", upload_root),
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
            )

            with common_patches[0], common_patches[1], common_patches[2]:
                with patch.object(
                    service_module,
                    "enqueue_and_wait_for_result",
                    new=AsyncMock(side_effect=AIAnalysisResultTimeoutError()),
                ):
                    with self.assertRaises(RequestTimeoutError):
                        await AIAnalysisService.get_or_create_ai_analysis(
                            db=AsyncMock(), record_id=10, model_name=MODEL_NAME
                        )

            with (
                patch.object(service_module, "UPLOAD_ROOT", upload_root),
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
                    service_module,
                    "enqueue_and_wait_for_result",
                    new=AsyncMock(side_effect=RedisClientError()),
                ),
            ):
                with self.assertRaises(AIQueueUnavailableError):
                    await AIAnalysisService.get_or_create_ai_analysis(
                        db=AsyncMock(), record_id=10, model_name=MODEL_NAME
                    )


if __name__ == "__main__":
    unittest.main()
