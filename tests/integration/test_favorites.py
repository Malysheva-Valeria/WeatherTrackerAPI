"""Інтеграційні тести улюблених міст."""


def test_favorites_require_auth(client):
    assert client.get("/favorites").status_code in (401, 403)


def test_add_favorite(client, auth_headers):
    resp = client.post("/favorites", json={"city": "Kyiv"}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["city"] == "Kyiv"


def test_add_duplicate_favorite_rejected(client, auth_headers):
    client.post("/favorites", json={"city": "Kyiv"}, headers=auth_headers)
    resp = client.post("/favorites", json={"city": "Kyiv"}, headers=auth_headers)
    assert resp.status_code == 400


def test_list_favorites(client, auth_headers):
    client.post("/favorites", json={"city": "Kyiv"}, headers=auth_headers)
    client.post("/favorites", json={"city": "Lviv"}, headers=auth_headers)

    resp = client.get("/favorites", headers=auth_headers)
    assert resp.status_code == 200
    cities = {f["city"] for f in resp.json()}
    assert cities == {"Kyiv", "Lviv"}


def test_remove_favorite(client, auth_headers):
    fav_id = client.post("/favorites", json={"city": "Kyiv"}, headers=auth_headers).json()["id"]
    resp = client.delete(f"/favorites/{fav_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert client.get("/favorites", headers=auth_headers).json() == []


def test_remove_missing_favorite_404(client, auth_headers):
    assert client.delete("/favorites/999999", headers=auth_headers).status_code == 404


def test_favorites_weather(client, auth_headers):
    client.post("/favorites", json={"city": "Kyiv"}, headers=auth_headers)
    client.post("/favorites", json={"city": "Lviv"}, headers=auth_headers)

    resp = client.get("/favorites/weather", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    for item in body:
        assert item["weather"] is not None
        assert item["weather"]["city"] == item["city"]
        assert item["error"] is None


def test_favorites_are_per_user(client, auth_headers, sample_user_data):
    client.post("/favorites", json={"city": "Kyiv"}, headers=auth_headers)

    # другий користувач не бачить чужих обраних
    client.post("/auth/register", json={
        "username": "other", "email": "other@example.com", "password": "otherpass123",
    })
    other_login = client.post("/auth/login", data={
        "username": "other", "password": "otherpass123",
    }).json()
    other_headers = {"Authorization": f"Bearer {other_login['access_token']}"}

    assert client.get("/favorites", headers=other_headers).json() == []
