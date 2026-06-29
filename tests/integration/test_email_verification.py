"""Тести підтвердження email."""
import re

from app.api.utils.email_client import outbox


def _token_from_outbox():
    """Дістати токен підтвердження з останнього листа (тестова скринька)."""
    assert outbox, "лист підтвердження не надіслано"
    body = outbox[-1].body
    match = re.search(r"token=([\w.\-]+)", body)
    assert match, f"токен не знайдено в листі: {body}"
    return match.group(1)


def test_register_sends_verification_email(client, sample_user_data):
    resp = client.post("/auth/register", json=sample_user_data)
    assert resp.status_code == 201
    assert len(outbox) == 1
    assert outbox[0].to == sample_user_data["email"]
    assert "token=" in outbox[0].body


def test_new_user_is_unverified(client, auth_headers):
    me = client.get("/auth/me", headers=auth_headers).json()
    assert me["is_verified"] is False


def test_verify_email_flow(client, sample_user_data, auth_headers):
    token = _token_from_outbox()
    resp = client.post("/auth/verify-email", json={"token": token})
    assert resp.status_code == 200

    me = client.get("/auth/me", headers=auth_headers).json()
    assert me["is_verified"] is True


def test_verify_email_invalid_token(client):
    assert client.post("/auth/verify-email", json={"token": "garbage"}).status_code == 400


def test_access_token_not_accepted_as_verify(client, sample_user_data):
    body = client.post("/auth/register", json=sample_user_data).json()
    # access-токен має type!=verify -> 400
    assert client.post("/auth/verify-email", json={"token": body["access_token"]}).status_code == 400


def test_resend_verification(client, auth_headers):
    outbox.clear()
    resp = client.post("/auth/resend-verification", headers=auth_headers)
    assert resp.status_code == 200
    assert len(outbox) == 1


def test_resend_verification_already_verified(client, sample_user_data, auth_headers):
    token = _token_from_outbox()
    client.post("/auth/verify-email", json={"token": token})
    # вже верифікований -> 400
    assert client.post("/auth/resend-verification", headers=auth_headers).status_code == 400
