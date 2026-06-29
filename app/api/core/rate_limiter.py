"""
Rate limiting для ендпоінтів аутентифікації (захист від брутфорсу).

Реалізація — лічильник у фіксованому вікні (fixed-window). Основне сховище —
Redis (атомарний INCR + EXPIRE), з прозорим in-memory fallback'ом, якщо Redis
недоступний — так само, як CacheService. Помилка Redis ніколи не валить запит.
"""
import logging
import time
from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Request, status
from redis.exceptions import RedisError

from app.api.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class RateLimiter:
    """Лічильник запитів на ключ у межах часового вікна."""

    def __init__(self) -> None:
        self._redis_enabled = True
        # ключ -> (count, reset_at_monotonic)
        self._memory: Dict[str, Tuple[int, float]] = {}

    async def hit(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """Зареєструвати звернення. Повертає (дозволено, поточний_лічильник)."""
        if self._redis_enabled:
            try:
                client = get_redis_client()
                count = await client.incr(key)
                if count == 1:
                    await client.expire(key, window)
                return count <= limit, int(count)
            except RedisError as exc:
                logger.warning("Redis недоступний, rate limiter -> in-memory: %s", exc)
                self._redis_enabled = False
        return self._memory_hit(key, limit, window)

    def _memory_hit(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        now = time.monotonic()
        count, reset_at = self._memory.get(key, (0, now + window))
        if now > reset_at:
            count, reset_at = 0, now + window
        count += 1
        self._memory[key] = (count, reset_at)
        return count <= limit, count


# Глобальний інстанс лімітера
rate_limiter = RateLimiter()


def rate_limit(limit: int, window: int):
    """Фабрика FastAPI-залежності, що обмежує частоту звернень по IP клієнта."""

    async def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{request.url.path}:{client_ip}"
        allowed, _ = await rate_limiter.hit(key, limit=limit, window=window)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Забагато запитів. Спробуйте пізніше.",
                headers={"Retry-After": str(window)},
            )

    return Depends(dependency)
