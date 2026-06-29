"""Тести журналу аудиту."""


def test_audit_requires_auth(client):
    assert client.get("/users/me/audit").status_code in (401, 403)


def test_register_and_login_are_audited(client, auth_headers):
    # auth_headers робить register + login
    resp = client.get("/users/me/audit", headers=auth_headers)
    assert resp.status_code == 200
    actions = {e["action"] for e in resp.json()}
    assert "register" in actions
    assert "login_success" in actions


def test_password_change_is_audited(client, sample_user_data, auth_headers):
    client.put("/users/me/password", json={
        "current_password": sample_user_data["password"],
        "new_password": "newStrongPass123",
    }, headers=auth_headers)

    actions = {e["action"] for e in client.get("/users/me/audit", headers=auth_headers).json()}
    assert "password_changed" in actions


def test_email_verification_is_audited(client, sample_user_data, auth_headers):
    import re

    from app.api.utils.email_client import outbox
    token = re.search(r"token=([\w.\-]+)", outbox[-1].body).group(1)
    client.post("/auth/verify-email", json={"token": token})

    actions = {e["action"] for e in client.get("/users/me/audit", headers=auth_headers).json()}
    assert "email_verified" in actions


def test_audit_entries_have_expected_shape(client, auth_headers):
    entries = client.get("/users/me/audit", headers=auth_headers).json()
    assert entries
    entry = entries[0]
    assert {"id", "action", "created_at"} <= set(entry)


def test_failed_login_is_audited(client, sample_user_data, db_session):
    client.post("/auth/register", json=sample_user_data)
    client.post("/auth/login", data={
        "username": sample_user_data["username"], "password": "wrong-pass",
    })

    from app.api.models.audit import AuditLog
    failed = db_session.query(AuditLog).filter(AuditLog.action == "login_failed").all()
    assert len(failed) >= 1
    assert "username=" in (failed[-1].detail or "")
