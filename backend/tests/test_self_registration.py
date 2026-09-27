def _valid_payload(**overrides):
    payload = {
        "full_name": "Aditi Sharma",
        "mobile_number": "9876543210",
        "email": "aditi.newteam@example.com",
        "college_name": "Test College",
        "degree_course": "B.Tech Computer Science",
        "team_name": "Team Quantum",
        "domain_slug": "cybersecurity-smart-homes",
        "team_size": 3,
        "members": [
            {"name": "Rohan Mehta", "phone": "9876500001"},
            {"name": "Sana Iqbal", "phone": "9876500002"},
        ],
    }
    payload.update(overrides)
    return payload


def test_registration_creates_team_with_correct_payment_amount(client, domains):
    resp = client.post("/api/registrations", json=_valid_payload())
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["team_name"] == "Team Quantum"
    assert body["team_size"] == 3
    assert body["payment_per_person_inr"] == 300
    assert body["payment_amount_inr"] == 900


def test_registration_rejects_duplicate_team_name(client, domains):
    client.post("/api/registrations", json=_valid_payload())
    resp = client.post(
        "/api/registrations",
        json=_valid_payload(email="someoneelse@example.com", team_name="team quantum"),
    )
    assert resp.status_code == 409


def test_registration_rejects_duplicate_email(client, domains):
    client.post("/api/registrations", json=_valid_payload())
    resp = client.post(
        "/api/registrations",
        json=_valid_payload(team_name="Team Other"),
    )
    assert resp.status_code == 409


def test_registration_rejects_invalid_domain(client, domains):
    resp = client.post("/api/registrations", json=_valid_payload(domain_slug="not-a-real-domain"))
    assert resp.status_code == 400


def test_registration_rejects_member_count_mismatch(client, domains):
    resp = client.post(
        "/api/registrations",
        json=_valid_payload(team_size=4, members=[{"name": "Only One", "phone": "9876500009"}]),
    )
    assert resp.status_code == 422


def test_registration_allows_solo_team_with_no_members(client, domains):
    resp = client.post(
        "/api/registrations",
        json=_valid_payload(team_name="Team Solo", team_size=1, members=[]),
    )
    assert resp.status_code == 200
    assert resp.json()["payment_amount_inr"] == 300


def test_check_team_name_availability(client, domains):
    resp = client.get("/api/registrations/check-team-name", params={"team_name": "Team Quantum"})
    assert resp.status_code == 200
    assert resp.json()["available"] is True

    client.post("/api/registrations", json=_valid_payload())

    resp = client.get("/api/registrations/check-team-name", params={"team_name": "team quantum"})
    assert resp.json()["available"] is False


def test_registered_team_can_activate_and_login(client, db_session, domains, monkeypatch):
    from tests.conftest import activate_participant, auth_headers

    resp = client.post("/api/registrations", json=_valid_payload())
    assert resp.status_code == 200

    token = activate_participant(
        client, monkeypatch, "aditi.newteam@example.com", "LeaderPass123!", db_session=db_session
    )
    team = client.get("/api/team", headers=auth_headers(token)).json()
    assert team["name"] == "Team Quantum"
    assert team["domain"]["slug"] == "cybersecurity-smart-homes"
    assert {m["name"] for m in team["members"]} == {"Rohan Mehta", "Sana Iqbal"}


def test_admin_can_toggle_payment_status(client, admin_user, domains):
    from tests.conftest import auth_headers, login

    resp = client.post("/api/registrations", json=_valid_payload())
    registration_id = resp.json()["registration_id"]

    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    resp = client.get("/api/admin/registrations", headers=auth_headers(admin_token))
    assert resp.json()[0]["payment_status"] == "pending"

    resp = client.put(
        f"/api/admin/registrations/{registration_id}/payment-status",
        headers=auth_headers(admin_token),
        json={"payment_status": "paid"},
    )
    assert resp.status_code == 200
    assert resp.json()["payment_status"] == "paid"


def test_participant_cannot_toggle_payment_status(client, db_session, domains, monkeypatch):
    from tests.conftest import activate_participant, auth_headers

    resp = client.post("/api/registrations", json=_valid_payload())
    registration_id = resp.json()["registration_id"]
    token = activate_participant(
        client, monkeypatch, "aditi.newteam@example.com", "LeaderPass123!", db_session=db_session
    )

    resp = client.put(
        f"/api/admin/registrations/{registration_id}/payment-status",
        headers=auth_headers(token),
        json={"payment_status": "paid"},
    )
    assert resp.status_code == 403
