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


def _submit_round1(client, token, doc_key, vid_key):
    return client.post(
        "/api/submissions",
        headers=auth_headers(token),
        json={
            "document": {
                "storage_key": doc_key,
                "original_filename": "round1.pdf",
                "content_type": "application/pdf",
                "file_size_bytes": 10,
            },
            "video": {
                "storage_key": vid_key,
                "original_filename": "demo.mp4",
                "content_type": "video/mp4",
                "file_size_bytes": 10,
            },
        },
    )


def test_merge_team_moves_members_discards_submissions_and_disables_leader(
    client, db_session, admin_user, domains, registrations_synced, round_settings, monkeypatch
):
    token_a = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    token_b = activate_participant(client, monkeypatch, "leader.b@example.com", "LeaderPass123!")

    # Team B submits — this must be discarded entirely by the merge.
    doc_key = _presign_and_upload(client, token_b, "document", "b.pdf", "application/pdf", b"%PDF-1.4 b")
    vid_key = _presign_and_upload(client, token_b, "video", "b.mp4", "video/mp4", b"b-video")
    resp = _submit_round1(client, token_b, doc_key, vid_key)
    assert resp.status_code == 200

    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    teams = client.get("/api/admin/teams", headers=auth_headers(admin_token)).json()
    team_a = next(t for t in teams if t["name"] == "Team A")
    team_b = next(t for t in teams if t["name"] == "Team B")
    team_b_members_before = len(team_b["members"])
    team_a_members_before = len(team_a["members"])

    resp = client.post(
        "/api/admin/teams/merge",
        headers=auth_headers(admin_token),
        json={"primary_team_id": team_a["id"], "secondary_team_id": team_b["id"]},
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert result["primary_team_id"] == team_a["id"]
    assert result["secondary_team_name"] == "Team B"
    assert result["members_moved"] == team_b_members_before
    assert result["submissions_discarded"] == 1
    assert result["secondary_leader_disabled"] is True

    # Team B is gone entirely.
    resp = client.get(f"/api/admin/teams/{team_b['id']}", headers=auth_headers(admin_token))
    assert resp.status_code == 404

    # Team A absorbed Team B's members and kept its own domain, with no submissions of its own.
    detail = client.get(f"/api/admin/teams/{team_a['id']}", headers=auth_headers(admin_token)).json()
    assert len(detail["team"]["members"]) == team_a_members_before + team_b_members_before
    assert detail["team"]["domain"]["name"] == "Healthcare"
    assert detail["submissions"] == []

    # Team B's leader can no longer log in.
    resp = client.post(
        "/api/auth/login", json={"email": "leader.b@example.com", "password": "LeaderPass123!"}
    )
    assert resp.status_code in (401, 403)


def test_merge_rejects_same_team(client, admin_user, domains, registrations_synced, monkeypatch):
    token_a = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    teams = client.get("/api/admin/teams", headers=auth_headers(admin_token)).json()
    team_a_id = teams[0]["id"]

    resp = client.post(
        "/api/admin/teams/merge",
        headers=auth_headers(admin_token),
        json={"primary_team_id": team_a_id, "secondary_team_id": team_a_id},
    )
    assert resp.status_code == 400


def test_merge_404_for_missing_team(client, admin_user, domains, registrations_synced, monkeypatch):
    token_a = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    teams = client.get("/api/admin/teams", headers=auth_headers(admin_token)).json()
    team_a_id = teams[0]["id"]

    resp = client.post(
        "/api/admin/teams/merge",
        headers=auth_headers(admin_token),
        json={"primary_team_id": team_a_id, "secondary_team_id": 999999},
    )
    assert resp.status_code == 404
