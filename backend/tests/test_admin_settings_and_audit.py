from datetime import datetime, timedelta, timezone

from tests.conftest import auth_headers, login


def test_admin_can_configure_deadline_and_it_is_enforced(client, admin_user, domains, round_settings, registrations_synced, monkeypatch):
    from tests.conftest import activate_participant

    admin_token = login(client, "admin@test.dev", "AdminPass123!")

    new_end = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    resp = client.put(
        "/api/admin/settings", headers=auth_headers(admin_token), json={"submission_end": new_end}
    )
    assert resp.status_code == 200
    returned = datetime.fromisoformat(resp.json()["submission_end"])
    assert abs((returned - datetime.fromisoformat(new_end)).total_seconds()) < 1

    participant_token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    resp = client.post(
        "/api/uploads/presign",
        headers=auth_headers(participant_token),
        json={"file_type": "document", "filename": "x.pdf", "content_type": "application/pdf", "file_size_bytes": 10},
    )
    assert resp.status_code == 403
    assert "closed" in resp.json()["detail"].lower()


def test_admin_action_is_audit_logged(client, admin_user, domains):
    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    resp = client.post(
        "/api/admin/domains",
        headers=auth_headers(admin_token),
        json={"slug": "newdomain", "name": "New Domain", "description": "d"},
    )
    assert resp.status_code == 200

    resp = client.get("/api/admin/audit-logs", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    actions = [row["action"] for row in resp.json()]
    assert "create_domain" in actions


def test_registration_sync_dedupes_on_rerun(client, admin_user, domains):
    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    resp1 = client.post("/api/admin/sync-registrations", headers=auth_headers(admin_token))
    assert resp1.status_code == 200
    assert resp1.json()["created"] == 2

    resp2 = client.post("/api/admin/sync-registrations", headers=auth_headers(admin_token))
    assert resp2.status_code == 200
    assert resp2.json()["created"] == 0
    assert resp2.json()["updated"] == 2
