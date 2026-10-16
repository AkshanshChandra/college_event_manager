from datetime import datetime, timezone

from app.models import Registration
from app.models.enums import PaymentStatus, RegistrationSource
from tests.conftest import activate_participant, auth_headers, login


def _presign_and_upload(client, token, file_type, filename, content_type, content: bytes):
    resp = client.post(
        "/api/uploads/presign",
        headers=auth_headers(token),
        json={
            "file_type": file_type,
            "filename": filename,
            "content_type": content_type,
            "file_size_bytes": len(content),
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    put_resp = client.put(body["upload_url"], headers=auth_headers(token), content=content)
    assert put_resp.status_code == 204, put_resp.text
    return body["storage_key"]


def _make_registration(
    db_session, domains, *, team_name, leader_name, leader_email, leader_phone, domain_slug,
    members, payment_status=PaymentStatus.PENDING,
):
    now = datetime.now(timezone.utc)
    registration = Registration(
        team_name=team_name,
        leader_name=leader_name,
        leader_email=leader_email,
        leader_phone=leader_phone,
        college="Test College",
        degree_course="B.Tech",
        domain_slug=domain_slug,
        team_size=1 + len(members),
        members_raw=members,
        registered_at=now,
        source=RegistrationSource.MANUAL,
        synced_at=now,
        payment_status=payment_status,
    )
    db_session.add(registration)
    db_session.commit()
    db_session.refresh(registration)
    return registration


def test_merge_two_unapproved_registrations_with_no_accounts(client, db_session, admin_user, domains):
    primary = _make_registration(
        db_session, domains,
        team_name="Primary Team", leader_name="P Leader", leader_email="p.leader@example.com",
        leader_phone="9000000001", domain_slug="healthcare",
        members=[{"name": "P Member", "phone": "9000000002"}],
    )
    secondary = _make_registration(
        db_session, domains,
        team_name="Dup Team", leader_name="S Leader", leader_email="s.leader@example.com",
        leader_phone="9000000003", domain_slug="fintech",
        members=[{"name": "S Member", "phone": "9000000004"}],
    )

    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    resp = client.post(
        "/api/admin/registrations/merge",
        headers=auth_headers(admin_token),
        json={"primary_registration_id": primary.id, "secondary_registration_id": secondary.id},
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert result["primary_registration_id"] == primary.id
    assert result["secondary_team_name"] == "Dup Team"
    assert result["members_moved"] == 2  # secondary's leader + its 1 member
    assert result["submissions_discarded"] == 0
    assert result["secondary_leader_disabled"] is False

    # Secondary registration is gone entirely — no lingering duplicate row.
    regs = client.get("/api/admin/registrations", headers=auth_headers(admin_token)).json()
    team_names = [r["team_name"] for r in regs]
    assert "Dup Team" not in team_names
    merged = next(r for r in regs if r["team_name"] == "Primary Team")
    assert merged["team_size"] == 4
    member_names = {m["name"] for m in merged["members"]}
    assert member_names == {"P Member", "S Leader", "S Member"}

    # Still just PENDING — merging never verifies payment or creates an account.
    assert merged["payment_status"] == "pending"
    assert merged["account_status"] == "not_created"


def test_merge_discards_secondary_submissions_and_disables_its_login(
    client, db_session, admin_user, domains, round_settings, monkeypatch
):
    primary = _make_registration(
        db_session, domains,
        team_name="Keeper", leader_name="Keeper Leader", leader_email="keeper@example.com",
        leader_phone="9000000005", domain_slug="healthcare", members=[],
        payment_status=PaymentStatus.PAID,
    )
    secondary = _make_registration(
        db_session, domains,
        team_name="Duplicate", leader_name="Dup Leader", leader_email="dup@example.com",
        leader_phone="9000000006", domain_slug="healthcare", members=[],
        payment_status=PaymentStatus.PAID,
    )

    token_dup = activate_participant(client, monkeypatch, "dup@example.com", "LeaderPass123!")
    doc_key = _presign_and_upload(client, token_dup, "document", "x.pdf", "application/pdf", b"%PDF-1.4 x")
    vid_key = _presign_and_upload(client, token_dup, "video", "x.mp4", "video/mp4", b"vid")
    resp = client.post(
        "/api/submissions",
        headers=auth_headers(token_dup),
        json={
            "document": {"storage_key": doc_key, "original_filename": "x.pdf", "content_type": "application/pdf", "file_size_bytes": 10},
            "video": {"storage_key": vid_key, "original_filename": "x.mp4", "content_type": "video/mp4", "file_size_bytes": 10},
        },
    )
    assert resp.status_code == 200, resp.text

    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    resp = client.post(
        "/api/admin/registrations/merge",
        headers=auth_headers(admin_token),
        json={"primary_registration_id": primary.id, "secondary_registration_id": secondary.id},
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert result["members_moved"] == 1  # just the secondary's leader, it had no extra members
    assert result["submissions_discarded"] == 1
    assert result["secondary_leader_disabled"] is True

    # The merged-away leader can no longer log in.
    resp = client.post("/api/auth/login", json={"email": "dup@example.com", "password": "LeaderPass123!"})
    assert resp.status_code in (401, 403)


def test_merge_rejects_same_registration(client, db_session, admin_user, domains):
    reg = _make_registration(
        db_session, domains,
        team_name="Solo", leader_name="Solo Leader", leader_email="solo@example.com",
        leader_phone="9000000007", domain_slug="healthcare", members=[],
    )
    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    resp = client.post(
        "/api/admin/registrations/merge",
        headers=auth_headers(admin_token),
        json={"primary_registration_id": reg.id, "secondary_registration_id": reg.id},
    )
    assert resp.status_code == 400


def test_merge_404_for_missing_registration(client, db_session, admin_user, domains):
    reg = _make_registration(
        db_session, domains,
        team_name="Solo Two", leader_name="Solo Leader", leader_email="solo2@example.com",
        leader_phone="9000000008", domain_slug="healthcare", members=[],
    )
    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    resp = client.post(
        "/api/admin/registrations/merge",
        headers=auth_headers(admin_token),
        json={"primary_registration_id": reg.id, "secondary_registration_id": 999999},
    )
    assert resp.status_code == 404


def test_merge_rejects_when_over_max_team_size(client, db_session, admin_user, domains):
    primary = _make_registration(
        db_session, domains,
        team_name="Big A", leader_name="A Leader", leader_email="a.leader@example.com",
        leader_phone="9000000009", domain_slug="healthcare",
        members=[{"name": "A2", "phone": "9000000010"}, {"name": "A3", "phone": "9000000011"}],
    )
    secondary = _make_registration(
        db_session, domains,
        team_name="Big B", leader_name="B Leader", leader_email="b.leader@example.com",
        leader_phone="9000000012", domain_slug="healthcare",
        members=[{"name": "B2", "phone": "9000000013"}],
    )
    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    resp = client.post(
        "/api/admin/registrations/merge",
        headers=auth_headers(admin_token),
        json={"primary_registration_id": primary.id, "secondary_registration_id": secondary.id},
    )
    assert resp.status_code == 400
