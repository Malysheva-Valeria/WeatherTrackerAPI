"""
Асинхронний Redis-клієнт для WeatherTracker API.

Клієнт створюється лениво (один на процес). Якщо Redis недоступний, виклики
вищого рівня (CacheService) деградують до in-memory кешу — застосунок працює
й без Redis.
"""
import logging
from typing import Optional

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional["aioredis.Redis"] = None


def get_redis_client() -> "aioredis.Redis":
    """Повертає (лениво створений) асинхронний Redis-клієнт."""
    global _client
    if _client is None:
        _client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _client


async def close_redis_client() -> None:
    """Закриває зʼєднання (використовується у lifespan на shutdown)."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
