"""Synchronous Redis client for the AI worker."""

from __future__ import annotations

import os

from redis import Redis


DEFAULT_REDIS_URL = "redis://localhost:6379/0"


def create_redis_client(redis_url: str | None = None) -> Redis:
    """Create a synchronous Redis client from ``REDIS_URL``."""

    return Redis.from_url(
        redis_url or os.getenv("REDIS_URL", DEFAULT_REDIS_URL),
        decode_responses=True,
        socket_timeout=None,
        health_check_interval=30,
    )
