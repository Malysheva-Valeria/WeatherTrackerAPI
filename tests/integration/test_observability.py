"""Тести cross-cutting: request id, security headers, формат помилок."""


def test_response_has_request_id(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID")


def test_request_id_is_echoed_when_provided(client):
    resp = client.get("/health", headers={"X-Request-ID": "my-trace-123"})
    assert resp.headers.get("X-Request-ID") == "my-trace-123"


def test_security_headers_present(client):
    resp = client.get("/health")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "no-referrer"


def test_error_response_includes_request_id(client):
    # 401/403 на захищеному ендпоінті
    resp = client.get("/users/me")
    assert resp.status_code in (401, 403)
    body = resp.json()
    assert "detail" in body
    assert "request_id" in body


def test_validation_error_includes_request_id(client):
    # невалідне тіло реєстрації -> 422 з єдиним форматом
    resp = client.post("/auth/register", json={"username": "x"})
    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body
    assert "request_id" in body


def test_not_found_has_consistent_shape(client, auth_headers):
    resp = client.delete("/favorites/999999", headers=auth_headers)
    assert resp.status_code == 404
    assert set(resp.json()) >= {"detail", "request_id"}
