"""Інтеграційні тести ендпоінтів /users через TestClient."""


def test_get_my_profile(client, sample_user_data, auth_headers):
    resp = client.get("/users/me", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == sample_user_data["username"]
    assert body["email"] == sample_user_data["email"]
    assert body["is_active"] is True


def test_get_my_profile_requires_auth(client):
    assert client.get("/users/me").status_code in (401, 403)


def test_update_my_profile(client, auth_headers):
    resp = client.put("/users/me", json={"first_name": "Valeria", "last_name": "M"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["first_name"] == "Valeria"
    assert body["full_name"] == "Valeria M"


def test_update_email_resets_verification(client, auth_headers):
    resp = client.put("/users/me", json={"email": "new@example.com"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "new@example.com"
    assert resp.json()["is_verified"] is False


def test_update_to_existing_email_conflicts(client, auth_headers):
    # реєструємо другого користувача
    client.post("/auth/register", json={
        "username": "other", "email": "other@example.com", "password": "otherpass123",
    })
    resp = client.put("/users/me", json={"email": "other@example.com"}, headers=auth_headers)
    assert resp.status_code == 400


def test_change_password_success(client, sample_user_data, auth_headers):
    resp = client.put("/users/me/password", json={
        "current_password": sample_user_data["password"],
        "new_password": "brandNewPass123",
    }, headers=auth_headers)
    assert resp.status_code == 200

    # старий пароль більше не працює, новий — працює
    assert client.post("/auth/login", data={
        "username": sample_user_data["username"], "password": sample_user_data["password"],
    }).status_code == 401
    assert client.post("/auth/login", data={
        "username": sample_user_data["username"], "password": "brandNewPass123",
    }).status_code == 200


def test_change_password_wrong_current(client, auth_headers):
    resp = client.put("/users/me/password", json={
        "current_password": "wrong-current", "new_password": "brandNewPass123",
    }, headers=auth_headers)
    assert resp.status_code == 400


def test_change_password_same_as_current(client, sample_user_data, auth_headers):
    resp = client.put("/users/me/password", json={
        "current_password": sample_user_data["password"],
        "new_password": sample_user_data["password"],
    }, headers=auth_headers)
    assert resp.status_code == 400


def test_delete_account_deactivates(client, auth_headers):
    resp = client.delete("/users/me", headers=auth_headers)
    assert resp.status_code == 200
    # після деактивації захищені ендпоінти недоступні
    # (get_user_by_token повертає None для неактивного -> 401)
    assert client.get("/users/me", headers=auth_headers).status_code in (400, 401, 403)


def test_get_user_by_id(client, auth_headers):
    me = client.get("/users/me", headers=auth_headers).json()
    resp = client.get(f"/users/{me['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == me["id"]


def test_get_user_by_id_not_found(client, auth_headers):
    assert client.get("/users/999999", headers=auth_headers).status_code == 404
