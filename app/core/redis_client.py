from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from shared.ai_queue_protocol import (
    AI_ANALYSIS_QUEUE_KEY,
    AIAnalysisResultMessage,
    AIAnalysisTaskMessage,
    build_result_channel,
)


class RedisClientError(Exception):
    """Raised when the AI queue cannot be reached or returns invalid data."""


class AIAnalysisResultTimeoutError(Exception):
    """Raised when a worker does not publish a final result in time."""


_redis_client: Redis | None = None


def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=False,
            socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
            health_check_interval=30,
        )
    return _redis_client


async def close_redis_client() -> None:
    global _redis_client
    client, _redis_client = _redis_client, None
    if client is not None:
        await client.aclose()


async def _result_messages(
    task: AIAnalysisTaskMessage,
) -> AsyncIterator[AIAnalysisResultMessage]:
    client = get_redis_client()
    pubsub = client.pubsub()
    channel = build_result_channel(task.job_id)

    try:
        # Subscribe before enqueueing so a fast worker cannot publish before the
        # app starts listening.
        await pubsub.subscribe(channel)
        await client.rpush(AI_ANALYSIS_QUEUE_KEY, task.to_json())

        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            try:
                result = AIAnalysisResultMessage.from_json(message["data"])
            except (KeyError, TypeError, ValueError) as exc:
                raise RedisClientError("Invalid AI worker result message.") from exc

            if result.job_id != task.job_id:
                continue
            yield result
            if result.is_done():
                return
    except RedisError as exc:
        raise RedisClientError("Redis AI queue is unavailable.") from exc
    finally:
        await pubsub.aclose()


async def enqueue_and_wait_for_result(
    task: AIAnalysisTaskMessage,
    *,
    timeout_seconds: float,
) -> AIAnalysisResultMessage:
    try:
        async with asyncio.timeout(timeout_seconds):
            async for result in _result_messages(task):
                if result.is_done():
                    return result
    except TimeoutError as exc:
        raise AIAnalysisResultTimeoutError() from exc

    raise RedisClientError("AI worker result stream ended unexpectedly.")
