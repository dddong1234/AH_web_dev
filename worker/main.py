"""Redis queue consumer for pneumonia prediction jobs."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from redis import Redis
from redis.exceptions import TimeoutError as RedisTimeoutError

from shared.ai_queue_protocol import (
    AI_ANALYSIS_QUEUE_KEY,
    AI_MODEL_NAME,
    AIAnalysisResultMessage,
    AIAnalysisTaskMessage,
    build_result_channel,
    make_failed_result,
    make_running_result,
    make_success_result,
)
from worker.model import load_prediction_model, predict_pneumonia
from worker.redis_client import create_redis_client


PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_ROOT = PROJECT_ROOT / "uploads"

logger = logging.getLogger(__name__)


def _publish_result(
    redis_client: Redis,
    result: AIAnalysisResultMessage,
) -> None:
    redis_client.publish(
        build_result_channel(result.job_id),
        result.to_json(),
    )


def _resolve_image_path(image_path: str) -> Path:
    path = Path(image_path)
    if path.is_absolute():
        raise ValueError("image_path must be relative to the uploads directory.")

    upload_root = UPLOAD_ROOT.resolve()
    resolved_path = (upload_root / path).resolve()
    if upload_root not in resolved_path.parents:
        raise ValueError("image_path must stay inside the uploads directory.")
    return resolved_path


def _validate_prediction(prediction: dict[str, Any]) -> tuple[bool, float, str]:
    is_pneumonia = prediction.get("is_pneumonia")
    confidence = prediction.get("confidence")
    heatmap_path = prediction.get("heatmap_path")

    if not isinstance(is_pneumonia, bool):
        raise ValueError("Prediction is missing a valid is_pneumonia value.")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise ValueError("Prediction is missing a valid confidence value.")
    if not 0.0 <= float(confidence) <= 1.0:
        raise ValueError("Prediction confidence must be between 0 and 1.")
    if not isinstance(heatmap_path, str) or not heatmap_path:
        raise ValueError("Prediction is missing a valid heatmap_path value.")

    return is_pneumonia, float(confidence), heatmap_path


def process_task(redis_client: Redis, task: AIAnalysisTaskMessage) -> None:
    """Run one prediction task and publish each state transition."""

    _publish_result(redis_client, make_running_result(task))

    try:
        if task.model_name != AI_MODEL_NAME:
            raise ValueError(f"Unsupported model_name: {task.model_name}")

        prediction = predict_pneumonia(
            _resolve_image_path(task.image_path),
            task.record_id,
        )
        is_pneumonia, confidence, heatmap_path = _validate_prediction(
            prediction
        )
        result = make_success_result(
            task,
            is_pneumonia=is_pneumonia,
            confidence=confidence,
            heatmap_path=heatmap_path,
        )
    except Exception as exc:
        logger.exception("AI analysis failed: job_id=%s", task.job_id)
        result = make_failed_result(
            task,
            error=str(exc) or exc.__class__.__name__,
        )

    _publish_result(redis_client, result)


def consume_next_task(redis_client: Redis, *, timeout: int = 0) -> bool:
    """Atomically take and process one task from the shared Redis queue."""

    try:
        queued_item = redis_client.brpop(
            AI_ANALYSIS_QUEUE_KEY,
            timeout=timeout,
        )
    except RedisTimeoutError:
        logger.warning(
            "Redis BRPOP timed out while waiting for queue=%s; continuing",
            AI_ANALYSIS_QUEUE_KEY,
        )
        return False

    if queued_item is None:
        return False

    _queue_key, raw_task = queued_item
    try:
        task = AIAnalysisTaskMessage.from_json(raw_task)
    except Exception:
        logger.exception("Discarding an invalid AI analysis task")
        return True

    process_task(redis_client, task)
    return True


def run_worker(redis_client: Redis) -> None:
    """Consume tasks until the worker process is stopped."""

    while True:
        consume_next_task(redis_client)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    redis_client = create_redis_client()
    try:
        redis_client.ping()
        load_prediction_model()
        logger.info("AI worker started; queue=%s", AI_ANALYSIS_QUEUE_KEY)
        run_worker(redis_client)
    finally:
        redis_client.close()


if __name__ == "__main__":
    main()
