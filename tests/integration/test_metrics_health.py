"""Тести метрик Prometheus та health-проб (liveness/readiness)."""


def test_liveness(client):
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


def test_readiness_ok(client):
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_metrics_endpoint(client):
    # робимо запит, щоб зʼявилися дані
    client.get("/health")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "http_requests_total" in resp.text
    assert "http_request_duration_seconds" in resp.text


def test_metrics_uses_route_template_not_raw_path(client, auth_headers):
    # звернення з id у шляху не має плодити унікальні серії
    client.delete("/favorites/123", headers=auth_headers)
    client.delete("/favorites/456", headers=auth_headers)
    body = client.get("/metrics").text
    # у метриках має бути шаблон, а не конкретні id
    assert "/favorites/{favorite_id}" in body
    assert "/favorites/123" not in body
