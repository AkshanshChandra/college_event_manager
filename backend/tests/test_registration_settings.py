from app.models import RegistrationSettings
from tests.conftest import auth_headers, login


def _valid_payload(**overrides):
    payload = {
        "full_name": "Aditi Sharma",
        "mobile_number": "9876543210",
        "email": "aditi.closedtest@example.com",
        "college_name": "Test College",
        "degree_course": "B.Tech Computer Science",
        "team_name": "Team Closed Test",
        "domain_slug": "cybersecurity-smart-homes",
        "team_size": 1,
        "members": [],
        "payment_method": "cash",
    }
    payload.update(overrides)
    return payload


def test_registration_open_by_default(client, domains):
    resp = client.get("/api/public/timeline")
    assert resp.status_code == 200
    assert resp.json()["registration_open"] is True

    resp = client.post("/api/registrations", json=_valid_payload())
    assert resp.status_code == 200, resp.text


def test_registration_rejected_when_closed(client, db_session, domains):
    db_session.add(RegistrationSettings(is_open=False))
    db_session.commit()

    resp = client.get("/api/public/timeline")
    assert resp.json()["registration_open"] is False

    resp = client.post("/api/registrations", json=_valid_payload())
    assert resp.status_code == 403
    assert "closed" in resp.json()["detail"].lower()


def test_admin_can_toggle_registration_settings(client, admin_user, domains):
    admin_token = login(client, "admin@test.dev", "AdminPass123!")

    resp = client.get("/api/admin/registration-settings", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert resp.json()["is_open"] is True

    resp = client.put(
        "/api/admin/registration-settings", headers=auth_headers(admin_token), json={"is_open": False}
    )
    assert resp.status_code == 200
    assert resp.json()["is_open"] is False

    resp = client.post("/api/registrations", json=_valid_payload(email="blocked@example.com", team_name="Blocked"))
    assert resp.status_code == 403

    resp = client.put(
        "/api/admin/registration-settings", headers=auth_headers(admin_token), json={"is_open": True}
    )
    assert resp.status_code == 200
    assert resp.json()["is_open"] is True

    resp = client.post("/api/registrations", json=_valid_payload(email="unblocked@example.com", team_name="Unblocked"))
    assert resp.status_code == 200, resp.text
