"""Інтеграційні тести ендпоінтів /api/v1/analytics через TestClient."""
import pytest

PREFIX = "/api/v1/analytics"


@pytest.fixture
def seeded(client, auth_headers):
    """Створює кілька погодних запитів, щоб аналітика мала з чим працювати."""
    for city in ("Kyiv", "Kyiv", "Lviv"):
        client.get("/weather/current", params={"city": city}, headers=auth_headers)
    return auth_headers


def test_summary_requires_auth(client):
    assert client.get(f"{PREFIX}/summary").status_code in (401, 403)


def test_summary(client, seeded):
    resp = client.get(f"{PREFIX}/summary", headers=seeded)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_requests"] >= 3
    assert "active_users_30d" in body


def test_user_stats(client, seeded):
    resp = client.get(f"{PREFIX}/user/stats", headers=seeded)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_requests"] >= 3
    # Kyiv має бути серед улюблених міст (2 запити)
    cities = {c["city"] for c in body["favorite_cities"]}
    assert "Kyiv" in cities


def test_popular_cities(client, seeded):
    resp = client.get(f"{PREFIX}/cities/popular", params={"limit": 5}, headers=seeded)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["popular_cities"], list)
    assert body["popular_cities"][0]["city"] == "Kyiv"  # найчастіше


def test_temperature_trends(client, seeded):
    resp = client.get(f"{PREFIX}/temperature/trends", params={"period_days": 30}, headers=seeded)
    assert resp.status_code == 200
    assert "summary" in resp.json()


def test_export_csv(client, seeded):
    resp = client.get(f"{PREFIX}/export/csv", headers=seeded)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "City" in resp.text  # заголовок CSV


def test_export_json(client, seeded):
    resp = client.get(f"{PREFIX}/export/json", headers=seeded)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_records"] >= 3
    assert isinstance(body["data"], list)


def test_admin_overview_forbidden_for_regular_user(client, seeded):
    # звичайний користувач не суперюзер -> 403
    assert client.get(f"{PREFIX}/admin/system-overview", headers=seeded).status_code == 403


def test_admin_overview_allowed_for_superuser(client, db_session, seeded):
    # робимо користувача суперюзером напряму в БД і перевіряємо доступ
    from app.api.models.user import User
    user = db_session.query(User).filter(User.username == "testuser").first()
    user.is_superuser = True
    db_session.commit()

    resp = client.get(f"{PREFIX}/admin/system-overview", headers=seeded)
    assert resp.status_code == 200
    assert "system_stats" in resp.json()
