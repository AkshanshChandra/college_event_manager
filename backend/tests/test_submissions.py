from datetime import datetime, timedelta, timezone

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


def test_full_submission_flow_and_versioning(client, domains, registrations_synced, round_settings, monkeypatch):
    token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")

    doc_key = _presign_and_upload(client, token, "document", "round1.pdf", "application/pdf", b"%PDF-1.4 x")
    vid_key = _presign_and_upload(client, token, "video", "demo.mp4", "video/mp4", b"fake-mp4-bytes")

    resp = _submit_round1(client, token, doc_key, vid_key)
    assert resp.status_code == 200, resp.text
    assert resp.json()["version"] == 1
    assert resp.json()["is_active_version"] is True

    doc_key2 = _presign_and_upload(client, token, "document", "round1_v2.pdf", "application/pdf", b"%PDF-1.4 y")
    resp2 = _submit_round1(client, token, doc_key2, vid_key)
    assert resp2.status_code == 200
    assert resp2.json()["version"] == 2

    state = client.get("/api/team/submission", headers=auth_headers(token)).json()
    assert state["participant_status"] == "submitted"
    assert len(state["versions"]) == 2
    assert state["active_submission"]["version"] == 2


def test_submission_rejected_after_deadline(client, db_session, domains, registrations_synced, monkeypatch):
    from app.models import CompetitionSettings

    db_session.add(
        CompetitionSettings(
            round_key="round_1",
            round_label="Round 1",
            submission_start=datetime.now(timezone.utc) - timedelta(days=10),
            submission_end=datetime.now(timezone.utc) - timedelta(days=1),
            allow_replacement=True,
            max_document_size_mb=1,
            max_video_size_mb=1,
            allowed_document_extensions="pdf",
            allowed_video_extensions="mp4",
        )
    )
    db_session.commit()

    token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    resp = client.post(
        "/api/uploads/presign",
        headers=auth_headers(token),
        json={"file_type": "document", "filename": "x.pdf", "content_type": "application/pdf", "file_size_bytes": 10},
    )
    assert resp.status_code == 403
    assert "closed" in resp.json()["detail"].lower()


def test_submission_rejected_before_window_opens(client, db_session, domains, registrations_synced, monkeypatch):
    from app.models import CompetitionSettings

    db_session.add(
        CompetitionSettings(
            round_key="round_1",
            round_label="Round 1",
            submission_start=datetime.now(timezone.utc) + timedelta(days=1),
            submission_end=datetime.now(timezone.utc) + timedelta(days=10),
            allow_replacement=True,
            max_document_size_mb=1,
            max_video_size_mb=1,
            allowed_document_extensions="pdf",
            allowed_video_extensions="mp4",
        )
    )
    db_session.commit()

    token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    resp = client.post(
        "/api/uploads/presign",
        headers=auth_headers(token),
        json={"file_type": "document", "filename": "x.pdf", "content_type": "application/pdf", "file_size_bytes": 10},
    )
    assert resp.status_code == 403
    assert "not open" in resp.json()["detail"].lower()


def test_file_validation_rejects_bad_extension(client, domains, registrations_synced, round_settings, monkeypatch):
    token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    resp = client.post(
        "/api/uploads/presign",
        headers=auth_headers(token),
        json={"file_type": "document", "filename": "malware.exe", "content_type": "application/octet-stream", "file_size_bytes": 10},
    )
    assert resp.status_code == 400
    assert "not supported" in resp.json()["detail"].lower()


def test_file_validation_rejects_oversized_file(client, domains, registrations_synced, round_settings, monkeypatch):
    token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    too_big = round_settings.max_document_size_mb * 1024 * 1024 + 1
    resp = client.post(
        "/api/uploads/presign",
        headers=auth_headers(token),
        json={"file_type": "document", "filename": "big.pdf", "content_type": "application/pdf", "file_size_bytes": too_big},
    )
    assert resp.status_code == 400
    assert "exceeds" in resp.json()["detail"].lower()


def test_team_a_cannot_access_team_bs_files(client, domains, registrations_synced, round_settings, monkeypatch):
    token_a = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    token_b = activate_participant(client, monkeypatch, "leader.b@example.com", "LeaderPass123!")

    doc_key_a = _presign_and_upload(client, token_a, "document", "a.pdf", "application/pdf", b"%PDF-1.4 a")
    vid_key_a = _presign_and_upload(client, token_a, "video", "a.mp4", "video/mp4", b"a-video")
    resp = _submit_round1(client, token_a, doc_key_a, vid_key_a)
    assert resp.status_code == 200

    # Team B tries to submit using Team A's storage keys.
    resp = _submit_round1(client, token_b, doc_key_a, vid_key_a)
    assert resp.status_code == 403

    # Team B tries to download Team A's file by guessing the storage key and
    # forging a signature — the download URL is only ever handed out by an
    # admin-only endpoint, so this must fail on signature verification.
    resp = client.get(
        f"/api/uploads/local-download/{doc_key_a}",
        params={"filename": "a.pdf", "expires": 9999999999, "sig": "forged"},
        headers=auth_headers(token_b),
    )
    assert resp.status_code == 403

    # Team B cannot see Team A's submission via their own submission state.
    state_b = client.get("/api/team/submission", headers=auth_headers(token_b)).json()
    assert state_b["active_submission"] is None


def test_admin_can_view_all_teams_and_submissions(
    client, admin_user, domains, registrations_synced, round_settings, monkeypatch
):
    token_a = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    doc_key = _presign_and_upload(client, token_a, "document", "a.pdf", "application/pdf", b"%PDF-1.4 a")
    vid_key = _presign_and_upload(client, token_a, "video", "a.mp4", "video/mp4", b"a-video")
    _submit_round1(client, token_a, doc_key, vid_key)

    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    resp = client.get("/api/admin/teams", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    # Only Team A has activated a portal account (teams are created lazily on
    # request-access), even though both teams are present in `registrations`.
    assert len(resp.json()) == 1

    resp = client.get("/api/admin/submissions", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["team_name"] == "Team A"

    submission_id = resp.json()[0]["submission_id"]
    detail = client.get(f"/api/admin/submissions/{submission_id}", headers=auth_headers(admin_token)).json()
    download_url = detail["files"][0]["download_url"]

    # The admin-issued presigned URL works with no Authorization header at all.
    resp = client.get(download_url)
    assert resp.status_code == 200
