"""Unit-тести CacheService (in-memory режим та graceful degradation)."""
import pytest

from app.api.services.cache_service import CacheService


@pytest.fixture
def cache():
    c = CacheService(default_ttl=600)
    c._redis_enabled = False  # форсуємо in-memory режим
    return c


@pytest.mark.asyncio
async def test_set_and_get(cache):
    await cache.set_json("k", {"a": 1})
    assert await cache.get_json("k") == {"a": 1}


@pytest.mark.asyncio
async def test_get_missing_returns_none(cache):
    assert await cache.get_json("absent") is None


@pytest.mark.asyncio
async def test_delete(cache):
    await cache.set_json("k", {"a": 1})
    await cache.delete("k")
    assert await cache.get_json("k") is None


@pytest.mark.asyncio
async def test_expired_entry_is_evicted(cache):
    await cache.set_json("k", {"a": 1}, ttl=0)  # негайно протермінований
    assert await cache.get_json("k") is None
    assert "k" not in cache._memory  # запис прибрано при читанні


@pytest.mark.asyncio
async def test_redis_error_falls_back_to_memory(monkeypatch):
    """Якщо Redis кидає помилку — сервіс деградує до in-memory без винятку."""
    from redis.exceptions import RedisError

    c = CacheService(default_ttl=600)
    c._redis_enabled = True

    class BrokenRedis:
        async def get(self, *a, **k):
            raise RedisError("down")

        async def set(self, *a, **k):
            raise RedisError("down")

    monkeypatch.setattr(
        "app.api.services.cache_service.get_redis_client", lambda: BrokenRedis()
    )

    # set не падає, перемикається на memory; get теж працює
    await c.set_json("k", {"v": 1})
    assert c._redis_enabled is False  # Redis вимкнено після помилки
    assert await c.get_json("k") == {"v": 1}
