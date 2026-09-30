from tests.conftest import auth_headers, login


def _base_payload(**overrides):
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
    return payload


def _presign_and_upload(client, filename="proof.png", content=b"fake png bytes"):
    resp = client.post(
        "/api/registrations/payment-screenshot/presign",
        json={
            "filename": filename,
            "content_type": "image/png",
            "file_size_bytes": len(content),
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    put_resp = client.put(body["upload_url"], content=content)
    assert put_resp.status_code == 204, put_resp.text
    return {
        "storage_key": body["storage_key"],
        "original_filename": filename,
        "content_type": "image/png",
        "file_size_bytes": len(content),
    }


def _register_online(client, **overrides):
    screenshot = _presign_and_upload(client)
    resp = client.post(
        "/api/registrations",
        json=_base_payload(payment_method="online", payment_screenshot=screenshot, **overrides),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_online_registration_starts_submitted_with_no_portal_access(client, domains):
    result = _register_online(client)
    assert result["payment_method"] == "online"
    assert result["payment_status"] == "submitted"

    resp = client.get(
        "/api/registrations/check-team-name", params={"team_name": "Team Payment"}
    )
    assert resp.json()["available"] is False  # name is reserved immediately

    # A screenshot is proof to review, not verification — no portal access yet.
    resp = client.post("/api/auth/request-access", json={"email": "vikram.payment@example.com"})
    assert resp.status_code == 403


def test_online_registration_screenshot_visible_to_admin(client, admin_user, domains):
    result = _register_online(client)

    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    resp = client.get("/api/admin/registrations", headers=auth_headers(admin_token))
    row = next(r for r in resp.json() if r["id"] == result["registration_id"])
    assert row["payment_status"] == "submitted"
    assert row["payment_method"] == "online"
    assert row["payment_screenshot_url"] is not None


def test_payment_screenshot_rejects_bad_file_type(client, domains):
    resp = client.post(
        "/api/registrations/payment-screenshot/presign",
        json={
            "filename": "malware.exe",
            "content_type": "application/octet-stream",
            "file_size_bytes": 100,
        },
    )
    assert resp.status_code == 400


def test_online_payment_requires_a_valid_pending_payment_storage_key(client, domains):
    resp = client.post(
        "/api/registrations",
        json=_base_payload(
            payment_method="online",
            payment_screenshot={
                "storage_key": "teams/1/document/not-a-payment-key.png",
                "original_filename": "proof.png",
                "content_type": "image/png",
                "file_size_bytes": 100,
            },
        ),
    )
    assert resp.status_code == 400


def test_cash_registration_starts_pending_with_no_screenshot(client, domains):
    resp = client.post(
        "/api/registrations",
        json=_base_payload(payment_method="cash", email="cash.payer@example.com", team_name="Team Cash"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["payment_method"] == "cash"
    assert body["payment_status"] == "pending"


def test_verifying_payment_grants_portal_access_immediately(client, admin_user, db_session, domains):
    result = _register_online(client)
    registration_id = result["registration_id"]
    email = "vikram.payment@example.com"

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


def test_admin_can_filter_registrations_by_payment_method(client, admin_user, domains):
    _register_online(client)
    client.post(
        "/api/registrations",
        json=_base_payload(payment_method="cash", email="cash.payer2@example.com", team_name="Team Cash Two"),
    )

    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    resp = client.get(
        "/api/admin/registrations", headers=auth_headers(admin_token), params={"payment_method": "cash"}
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["payment_method"] == "cash"


def test_online_payment_screenshot_is_optional(client, domains):
    resp = client.post(
        "/api/registrations",
        json=_base_payload(payment_method="online", email="online.noproof@example.com", team_name="Team No Proof"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["payment_method"] == "online"
    assert body["payment_status"] == "pending"


def test_admin_can_filter_registrations_by_screenshot_presence(client, admin_user, domains):
    _register_online(client)  # has a screenshot
    client.post(
        "/api/registrations",
        json=_base_payload(
            payment_method="online", email="online.noproof2@example.com", team_name="Team No Proof Two"
        ),
    )

    admin_token = login(client, "admin@test.dev", "AdminPass123!")

    resp = client.get(
        "/api/admin/registrations", headers=auth_headers(admin_token), params={"has_screenshot": "true"}
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["payment_screenshot_url"] is not None

    resp = client.get(
        "/api/admin/registrations", headers=auth_headers(admin_token), params={"has_screenshot": "false"}
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["team_name"] == "Team No Proof Two"
