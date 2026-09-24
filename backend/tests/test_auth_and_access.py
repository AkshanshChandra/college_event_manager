from tests.conftest import activate_participant, auth_headers, login


def test_unregistered_email_cannot_request_access(client, domains):
    resp = client.post("/api/auth/request-access", json={"email": "ghost@example.com"})
    assert resp.status_code == 404


def test_unregistered_email_cannot_create_participant_account(client, db_session, domains):
    from app.models import User

    client.post("/api/auth/request-access", json={"email": "ghost@example.com"})
    assert db_session.query(User).filter_by(email="ghost@example.com").one_or_none() is None


def test_registered_email_activation_and_login_flow(client, domains, registrations_synced, monkeypatch):
    token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    assert token

    login_token = login(client, "leader.a@example.com", "LeaderPass123!")
    resp = client.get("/api/auth/me", headers=auth_headers(login_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "leader.a@example.com"
    assert body["role"] == "participant"


def test_wrong_password_is_rejected(client, domains, registrations_synced, monkeypatch):
    activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    resp = client.post(
        "/api/auth/login", json={"email": "leader.a@example.com", "password": "WrongPassword!"}
    )
    assert resp.status_code == 401


def test_inactive_account_cannot_login(client, domains, registrations_synced):
    """An account that exists (e.g. via a stray User row) but was never activated can't log in."""
    from app.models import User
    from app.models.enums import AccountStatus, UserRole

    resp = client.post("/api/auth/request-access", json={"email": "leader.a@example.com"})
    assert resp.status_code == 204

    resp = client.post(
        "/api/auth/login", json={"email": "leader.a@example.com", "password": "anything"}
    )
    assert resp.status_code == 401


def test_expired_or_invalid_activation_token_rejected(client, domains, registrations_synced):
    resp = client.post("/api/auth/activate", json={"token": "not-a-real-token", "password": "x" * 10})
    assert resp.status_code == 400


def test_participant_cannot_access_admin_apis(client, domains, registrations_synced, monkeypatch):
    token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    resp = client.get("/api/admin/dashboard", headers=auth_headers(token))
    assert resp.status_code == 403

    resp = client.get("/api/admin/teams", headers=auth_headers(token))
    assert resp.status_code == 403

    resp = client.post("/api/admin/sync-registrations", headers=auth_headers(token))
    assert resp.status_code == 403


def test_admin_cannot_use_participant_only_routes_as_a_team(client, admin_user):
    token = login(client, "admin@test.dev", "AdminPass123!")
    resp = client.get("/api/team", headers=auth_headers(token))
    assert resp.status_code == 403
