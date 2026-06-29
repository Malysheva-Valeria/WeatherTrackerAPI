"""
CacheService — кеш JSON-значень з Redis як основним сховищем та in-memory
fallback'ом.

Дизайн: будь-яка помилка Redis НЕ повинна валити запит. Якщо Redis недоступний,
сервіс прозоро перемикається на локальний словник з TTL. Завдяки цьому застосунок
(і тести) працюють однаково з Redis і без нього.
"""
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

from redis.exceptions import RedisError

from app.api.utils.redis_client import get_redis_client
from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Асинхронний кеш JSON-значень (Redis + in-memory fallback)."""

    def __init__(self, default_ttl: Optional[int] = None):
        self.default_ttl = default_ttl if default_ttl is not None else settings.CACHE_TTL
        self._redis_enabled = True
        # ключ -> (expires_at_epoch, value)
        self._memory: Dict[str, Tuple[float, Any]] = {}

    async def get_json(self, key: str) -> Optional[Any]:
        """Повертає значення з кешу або None."""
        if self._redis_enabled:
            try:
                raw = await get_redis_client().get(key)
                if raw is not None:
                    return json.loads(raw)
                return None
            except RedisError as exc:
                self._disable_redis(exc)
        return self._memory_get(key)

    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Зберігає значення в кеш на ttl секунд."""
        ttl = ttl if ttl is not None else self.default_ttl
        if self._redis_enabled:
            try:
                await get_redis_client().set(key, json.dumps(value, default=str), ex=ttl)
                return
            except RedisError as exc:
                self._disable_redis(exc)
        self._memory_set(key, value, ttl)

    async def delete(self, key: str) -> None:
        if self._redis_enabled:
            try:
                await get_redis_client().delete(key)
                return
            except RedisError as exc:
                self._disable_redis(exc)
        self._memory.pop(key, None)

    # --- внутрішнє ---------------------------------------------------------
    def _disable_redis(self, exc: Exception) -> None:
        # Логуємо один раз і переходимо на in-memory, щоб не спамити логи.
        logger.warning("Redis недоступний, кеш переходить на in-memory: %s", exc)
        self._redis_enabled = False

    def _memory_get(self, key: str) -> Optional[Any]:
        entry = self._memory.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            self._memory.pop(key, None)
            return None
        return value

    def _memory_set(self, key: str, value: Any, ttl: int) -> None:
        self._memory[key] = (time.monotonic() + ttl, value)


# Глобальний інстанс кеш-сервісу
cache_service = CacheService()


def get_cache_service() -> CacheService:
    return cache_service
