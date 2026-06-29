"""Тести refresh-токенів з ротацією та відкликанням."""


def _login(client, sample_user_data):
    client.post("/auth/register", json=sample_user_data)
    resp = client.post("/auth/login", data={
        "username": sample_user_data["username"],
        "password": sample_user_data["password"],
    })
    assert resp.status_code == 200
    return resp.json()


def test_login_returns_refresh_token(client, sample_user_data):
    body = _login(client, sample_user_data)
    assert body["refresh_token"]
    assert body["access_token"]


def test_refresh_rotates_tokens(client, sample_user_data):
    body = _login(client, sample_user_data)
    old_refresh = body["refresh_token"]

    resp = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 200
    new = resp.json()
    assert new["access_token"] and new["refresh_token"]
    # новий refresh відрізняється від старого (ротація)
    assert new["refresh_token"] != old_refresh


def test_old_refresh_token_invalid_after_rotation(client, sample_user_data):
    body = _login(client, sample_user_data)
    old_refresh = body["refresh_token"]

    # перше використання — ок
    assert client.post("/auth/refresh", json={"refresh_token": old_refresh}).status_code == 200
    # повторне використання того ж токена — заборонено (відкликано при ротації)
    assert client.post("/auth/refresh", json={"refresh_token": old_refresh}).status_code == 401


def test_new_refresh_token_works(client, sample_user_data):
    body = _login(client, sample_user_data)
    rotated = client.post("/auth/refresh", json={"refresh_token": body["refresh_token"]}).json()
    # новим refresh можна оновитися знову
    assert client.post("/auth/refresh", json={"refresh_token": rotated["refresh_token"]}).status_code == 200


def test_invalid_refresh_token_rejected(client):
    assert client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"}).status_code == 401


def test_access_token_cannot_be_used_as_refresh(client, sample_user_data):
    body = _login(client, sample_user_data)
    # access-токен має type!=refresh -> відхиляється
    assert client.post("/auth/refresh", json={"refresh_token": body["access_token"]}).status_code == 401


def test_logout_revokes_refresh_token(client, sample_user_data):
    body = _login(client, sample_user_data)
    refresh = body["refresh_token"]

    out = client.post("/auth/logout", json={"refresh_token": refresh})
    assert out.status_code == 200
    assert out.json()["revoked"] is True

    # після logout цим refresh оновитися не можна
    assert client.post("/auth/refresh", json={"refresh_token": refresh}).status_code == 401
