"""
Інтеграційні тести API через FastAPI TestClient.

На відміну від старих файлів, що стукали в живий сервер на 127.0.0.1:8000,
ці тести підіймають застосунок у памʼяті (фікстура `client` з conftest) та
використовують SQLite-базу, тож виконуються будь-де і в CI.
"""


# ---------------------------------------------------------------------------
# Службові ендпоінти
# ---------------------------------------------------------------------------
def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "WeatherTracker" in resp.json()["message"]


# ---------------------------------------------------------------------------
# Аутентифікація
# ---------------------------------------------------------------------------
def test_register_success(client, sample_user_data):
    resp = client.post("/auth/register", json=sample_user_data)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["user"]["username"] == sample_user_data["username"]
    assert "access_token" in body


def test_register_duplicate_returns_400(client, sample_user_data):
    assert client.post("/auth/register", json=sample_user_data).status_code == 201
    resp = client.post("/auth/register", json=sample_user_data)
    assert resp.status_code == 400


def test_register_weak_password_returns_400(client):
    # Пароль проходить за довжиною (8 символів), але не містить літери —
    # це ловить саме перевірка сили пароля в сервісі (400), не схема (422).
    resp = client.post("/auth/register", json={
        "username": "weakuser",
        "email": "weak@example.com",
        "password": "12345678",
    })
    assert resp.status_code == 400


def test_login_success(client, sample_user_data):
    client.post("/auth/register", json=sample_user_data)
    resp = client.post("/auth/login", data={
        "username": sample_user_data["username"],
        "password": sample_user_data["password"],
    })
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client, sample_user_data):
    client.post("/auth/register", json=sample_user_data)
    resp = client.post("/auth/login", data={
        "username": sample_user_data["username"],
        "password": "totally-wrong",
    })
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/auth/me")
    assert resp.status_code in (401, 403)


def test_me_returns_current_user(client, sample_user_data, auth_headers):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == sample_user_data["username"]


# ---------------------------------------------------------------------------
# Погода (mock-режим, бо OPENWEATHER_API_KEY не заданий у тестах)
# ---------------------------------------------------------------------------
def test_current_weather_requires_auth(client):
    resp = client.get("/weather/current", params={"city": "Kyiv"})
    assert resp.status_code in (401, 403)


def test_current_weather_returns_mock_data(client, auth_headers):
    resp = client.get("/weather/current", params={"city": "Kyiv"}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["city"] == "Kyiv"
    assert body["mock"] is True
    # типи булевих полів — справжні bool, а не рядки
    assert isinstance(body["cached"], bool)


def test_current_weather_uses_cache_on_second_call(client, auth_headers):
    first = client.get("/weather/current", params={"city": "Dnipro"}, headers=auth_headers)
    second = client.get("/weather/current", params={"city": "Dnipro"}, headers=auth_headers)
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["cached"] is False
    # друга відповідь береться з кешу
    assert second.json()["cached"] is True


def test_weather_history_records_request(client, auth_headers):
    client.get("/weather/current", params={"city": "Lviv"}, headers=auth_headers)
    client.get("/weather/current", params={"city": "Odesa"}, headers=auth_headers)

    resp = client.get("/weather/history", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    cities = {item["city"] for item in body["items"]}
    assert {"Lviv", "Odesa"} <= cities


def test_weather_history_city_filter(client, auth_headers):
    client.get("/weather/current", params={"city": "Lviv"}, headers=auth_headers)
    client.get("/weather/current", params={"city": "Odesa"}, headers=auth_headers)

    resp = client.get("/weather/history", params={"city": "Lviv"}, headers=auth_headers)
    assert resp.status_code == 200
    assert all("lviv" in item["city"].lower() for item in resp.json()["items"])


def test_weather_stats(client, auth_headers):
    client.get("/weather/current", params={"city": "Kyiv"}, headers=auth_headers)
    resp = client.get("/weather/stats", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total_requests"] >= 1


def test_delete_history_item(client, auth_headers):
    client.get("/weather/current", params={"city": "Kyiv"}, headers=auth_headers)
    history = client.get("/weather/history", headers=auth_headers).json()
    request_id = history["items"][0]["id"]

    resp = client.delete(f"/weather/history/{request_id}", headers=auth_headers)
    assert resp.status_code == 200

    after = client.get("/weather/history", headers=auth_headers).json()
    assert all(item["id"] != request_id for item in after["items"])


def test_delete_missing_history_item_returns_404(client, auth_headers):
    resp = client.delete("/weather/history/999999", headers=auth_headers)
    assert resp.status_code == 404


def test_clear_history(client, auth_headers):
    client.get("/weather/current", params={"city": "Kyiv"}, headers=auth_headers)
    client.get("/weather/current", params={"city": "Lviv"}, headers=auth_headers)

    resp = client.delete("/weather/history", headers=auth_headers)
    assert resp.status_code == 200

    after = client.get("/weather/history", headers=auth_headers).json()
    assert after["total"] == 0


# ---------------------------------------------------------------------------
# Аналітика
# ---------------------------------------------------------------------------
def test_analytics_summary_requires_auth(client):
    resp = client.get("/api/v1/analytics/summary")
    assert resp.status_code in (401, 403)


def test_analytics_summary_authorized(client, auth_headers):
    client.get("/weather/current", params={"city": "Kyiv"}, headers=auth_headers)
    resp = client.get("/api/v1/analytics/summary", headers=auth_headers)
    assert resp.status_code == 200
    assert "total_requests" in resp.json()
