"""Тести rate limiting на ендпоінтах аутентифікації."""
import pytest

from app.api.core.rate_limiter import RateLimiter


# --- Unit: логіка лічильника ------------------------------------------------
@pytest.mark.asyncio
async def test_rate_limiter_allows_up_to_limit():
    rl = RateLimiter()
    rl._redis_enabled = False
    results = [await rl.hit("k", limit=3, window=60) for _ in range(4)]
    allowed = [r[0] for r in results]
    assert allowed == [True, True, True, False]


@pytest.mark.asyncio
async def test_rate_limiter_keys_are_independent():
    rl = RateLimiter()
    rl._redis_enabled = False
    await rl.hit("a", limit=1, window=60)
    blocked_a, _ = await rl.hit("a", limit=1, window=60)
    allowed_b, _ = await rl.hit("b", limit=1, window=60)
    assert blocked_a is False
    assert allowed_b is True


# --- Integration: 429 на login ---------------------------------------------
def test_login_is_rate_limited(client, sample_user_data):
    client.post("/auth/register", json=sample_user_data)

    statuses = []
    for _ in range(7):  # ліміт за замовчуванням — 5
        r = client.post("/auth/login", data={
            "username": sample_user_data["username"],
            "password": "wrong-on-purpose",
        })
        statuses.append(r.status_code)

    assert 429 in statuses
    # перші спроби проходять валідацію (401), далі — блок (429)
    assert statuses[0] == 401
    assert statuses[-1] == 429


def test_rate_limit_sets_retry_after_header(client, sample_user_data):
    client.post("/auth/register", json=sample_user_data)
    last = None
    for _ in range(7):
        last = client.post("/auth/login", data={
            "username": sample_user_data["username"], "password": "x",
        })
    assert last.status_code == 429
    assert "retry-after" in {k.lower() for k in last.headers}


def test_rate_limit_isolated_between_tests(client, sample_user_data):
    # Завдяки скиданню лічильника між тестами цей логін успішний,
    # навіть якщо попередній тест вичерпав ліміт.
    client.post("/auth/register", json=sample_user_data)
    resp = client.post("/auth/login", data={
        "username": sample_user_data["username"],
        "password": sample_user_data["password"],
    })
    assert resp.status_code == 200
