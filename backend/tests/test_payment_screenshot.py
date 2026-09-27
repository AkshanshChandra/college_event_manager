from tests.conftest import auth_headers, login


def _register(client, **overrides):
    payload = {
        "full_name": "Vikram Singh",
        "mobile_number": "9123456780",
        "email": "vikram.payment@example.com",
        "college_name": "IIT Delhi",
        "degree_course": "B.Tech",
        "team_name": "Team Payment",
        "domain_slug": "cybersecurity-smart-homes",
        "team_size": 1,
        "members": [],
    }
    payload.update(overrides)
    resp = client.post("/api/registrations", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _presign_and_upload(client, registration_id, email, filename="proof.png", content=b"fake png bytes"):
    resp = client.post(
        f"/api/registrations/{registration_id}/payment-screenshot/presign",
        json={
            "email": email,
            "filename": filename,
            "content_type": "image/png",
            "file_size_bytes": len(content),
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    put_resp = client.put(body["upload_url"], content=content)
    assert put_resp.status_code == 204, put_resp.text
    return body["storage_key"]


def test_registration_starts_with_payment_pending_and_no_portal_access(client, domains):
    result = _register(client)
    resp = client.get(
        "/api/registrations/check-team-name", params={"team_name": "Team Payment"}
    )
    assert resp.json()["available"] is False  # name is reserved immediately

    # No payment proof yet: self-serve portal access must be refused.
    resp = client.post("/api/auth/request-access", json={"email": "vikram.payment@example.com"})
    assert resp.status_code == 403
    assert result["registration_id"]


def test_payment_screenshot_upload_moves_status_to_submitted(client, admin_user, domains):
    result = _register(client)
    registration_id = result["registration_id"]
    email = "vikram.payment@example.com"

    storage_key = _presign_and_upload(client, registration_id, email)

    resp = client.post(
        f"/api/registrations/{registration_id}/payment-screenshot/confirm",
        json={
            "email": email,
            "storage_key": storage_key,
            "original_filename": "proof.png",
            "content_type": "image/png",
            "file_size_bytes": 14,
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["payment_status"] == "submitted"

    # Still no portal access — a screenshot is proof to review, not verification.
    resp = client.post("/api/auth/request-access", json={"email": email})
    assert resp.status_code == 403

    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    resp = client.get("/api/admin/registrations", headers=auth_headers(admin_token))
    row = next(r for r in resp.json() if r["id"] == registration_id)
    assert row["payment_status"] == "submitted"
    assert row["payment_screenshot_url"] is not None


def test_payment_screenshot_wrong_email_is_rejected(client, domains):
    result = _register(client)
    registration_id = result["registration_id"]

    resp = client.post(
        f"/api/registrations/{registration_id}/payment-screenshot/presign",
        json={
            "email": "someone-else@example.com",
            "filename": "proof.png",
            "content_type": "image/png",
            "file_size_bytes": 100,
        },
    )
    assert resp.status_code == 404


def test_payment_screenshot_rejects_bad_file_type(client, domains):
    result = _register(client)
    registration_id = result["registration_id"]

    resp = client.post(
        f"/api/registrations/{registration_id}/payment-screenshot/presign",
        json={
            "email": "vikram.payment@example.com",
            "filename": "malware.exe",
            "content_type": "application/octet-stream",
            "file_size_bytes": 100,
        },
    )
    assert resp.status_code == 400


def test_verifying_payment_grants_portal_access_immediately(client, admin_user, db_session, domains):
    result = _register(client)
    registration_id = result["registration_id"]
    email = "vikram.payment@example.com"
    storage_key = _presign_and_upload(client, registration_id, email)
    client.post(
        f"/api/registrations/{registration_id}/payment-screenshot/confirm",
        json={
            "email": email,
            "storage_key": storage_key,
            "original_filename": "proof.png",
            "content_type": "image/png",
            "file_size_bytes": 14,
        },
    )

    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    resp = client.put(
        f"/api/admin/registrations/{registration_id}/payment-status",
        headers=auth_headers(admin_token),
        json={"payment_status": "paid"},
    )
    assert resp.status_code == 200
    assert resp.json()["payment_status"] == "paid"

    from app.models import User

    db_session.expire_all()
    assert db_session.query(User).filter_by(email=email).one_or_none() is not None
