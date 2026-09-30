from tests.conftest import auth_headers, login


def _register_cash(client, **overrides):
    payload = {
        "full_name": "Priya Rao",
        "mobile_number": "9123456781",
        "email": "priya.rao@example.com",
        "college_name": "IIT Bombay",
        "degree_course": "B.Tech",
        "team_name": "Team Edit",
        "domain_slug": "cybersecurity-smart-homes",
        "team_size": 2,
        "members": [{"name": "Kabir Shah", "phone": "9123456782"}],
        "payment_method": "cash",
    }
    payload.update(overrides)
    resp = client.post("/api/registrations", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _edit_payload(**overrides):
    payload = {
        "team_name": "Team Edit",
        "leader_name": "Priya Rao",
        "leader_email": "priya.rao@example.com",
        "leader_phone": "9123456781",
        "college": "IIT Bombay",
        "degree_course": "B.Tech",
        "domain_slug": "cybersecurity-smart-homes",
        "team_size": 2,
        "members": [{"name": "Kabir Shah", "phone": "9123456782"}],
    }
    payload.update(overrides)
    return payload


def test_admin_can_edit_registration_details(client, admin_user, domains):
    result = _register_cash(client)
    admin_token = login(client, "admin@test.dev", "AdminPass123!")

    resp = client.put(
        f"/api/admin/registrations/{result['registration_id']}",
        headers=auth_headers(admin_token),
        json=_edit_payload(leader_email="priya.corrected@example.com", college="IIT Delhi"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["leader_email"] == "priya.corrected@example.com"
    assert body["college"] == "IIT Delhi"


def test_edit_rejects_team_name_already_used_by_another_registration(client, admin_user, domains):
    _register_cash(client)
    other = _register_cash(client, email="other@example.com", team_name="Other Team")
    admin_token = login(client, "admin@test.dev", "AdminPass123!")

    resp = client.put(
        f"/api/admin/registrations/{other['registration_id']}",
        headers=auth_headers(admin_token),
        json=_edit_payload(team_name="Team Edit", leader_email="other@example.com"),
    )
    assert resp.status_code == 409


def test_edit_rejects_member_count_mismatch(client, admin_user, domains):
    result = _register_cash(client)
    admin_token = login(client, "admin@test.dev", "AdminPass123!")

    resp = client.put(
        f"/api/admin/registrations/{result['registration_id']}",
        headers=auth_headers(admin_token),
        json=_edit_payload(team_size=3, members=[{"name": "Kabir Shah", "phone": "9123456782"}]),
    )
    assert resp.status_code == 422


def test_edit_keeps_existing_team_and_account_in_sync(client, admin_user, db_session, domains):
    result = _register_cash(client)
    registration_id = result["registration_id"]
    admin_token = login(client, "admin@test.dev", "AdminPass123!")

    # Verify payment first, which creates the Team/TeamMember/User rows.
    client.put(
        f"/api/admin/registrations/{registration_id}/payment-status",
        headers=auth_headers(admin_token),
        json={"payment_status": "paid"},
    )

    resp = client.put(
        f"/api/admin/registrations/{registration_id}",
        headers=auth_headers(admin_token),
        json=_edit_payload(
            leader_email="priya.newaddress@example.com",
            team_name="Team Edit Renamed",
            members=[{"name": "Kabir Renamed", "phone": "9123456782"}],
        ),
    )
    assert resp.status_code == 200, resp.text

    from app.models import Team, User

    db_session.expire_all()
    team = db_session.query(Team).filter_by(registration_id=registration_id).one()
    assert team.name == "Team Edit Renamed"
    assert {m.name for m in team.members} == {"Kabir Renamed"}
    assert db_session.query(User).filter_by(email="priya.rao@example.com").one_or_none() is None
    assert db_session.query(User).filter_by(email="priya.newaddress@example.com").one_or_none() is not None


def test_resend_email_sends_activation_link(client, admin_user, monkeypatch, domains):
    result = _register_cash(client)
    registration_id = result["registration_id"]
    admin_token = login(client, "admin@test.dev", "AdminPass123!")

    client.put(
        f"/api/admin/registrations/{registration_id}/payment-status",
        headers=auth_headers(admin_token),
        json={"payment_status": "paid"},
    )

    captured = {}

    def fake_send(to, team_name, activation_url):
        captured["to"] = to
        captured["url"] = activation_url

    monkeypatch.setattr("app.services.accounts.send_activation_email", fake_send)

    resp = client.post(
        f"/api/admin/registrations/{registration_id}/resend-email",
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 204, resp.text
    assert captured["to"] == "priya.rao@example.com"
    assert captured["url"]


def test_participant_cannot_edit_registrations(client, db_session, domains, monkeypatch):
    from tests.conftest import activate_participant

    result = _register_cash(client)
    registration_id = result["registration_id"]

    token = activate_participant(
        client, monkeypatch, "priya.rao@example.com", "LeaderPass123!", db_session=db_session
    )

    resp = client.put(
        f"/api/admin/registrations/{registration_id}",
        headers=auth_headers(token),
        json=_edit_payload(),
    )
    assert resp.status_code == 403
