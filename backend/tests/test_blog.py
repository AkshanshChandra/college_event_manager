from tests.conftest import activate_participant, auth_headers, login


def test_admin_blog_crud_and_visibility_after_publish(
    client, admin_user, db_session, domains, registrations_synced, monkeypatch
):
    admin_token = login(client, "admin@test.dev", "AdminPass123!")

    resp = client.post(
        "/api/admin/blogs",
        headers=auth_headers(admin_token),
        json={
            "domain_id": domains["healthcare"].id,
            "title": "Inside Healthcare Innovation",
            "content": "Some background reading on the domain.",
            "status": "draft",
        },
    )
    assert resp.status_code == 200, resp.text
    blog_id = resp.json()["id"]

    participant_token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    resp = client.get("/api/team/blog", headers=auth_headers(participant_token))
    assert resp.status_code == 200
    assert resp.json() is None

    resp = client.put(
        f"/api/admin/blogs/{blog_id}/publish",
        headers=auth_headers(admin_token),
        params={"status": "published"},
    )
    assert resp.status_code == 200

    resp = client.get("/api/team/blog", headers=auth_headers(participant_token))
    assert resp.status_code == 200
    assert resp.json()["title"] == "Inside Healthcare Innovation"


def test_participant_only_sees_own_domain_blog(
    client, db_session, domains, registrations_synced, monkeypatch
):
    from app.models import Blog
    from app.models.enums import PublishStatus

    db_session.add_all(
        [
            Blog(
                domain_id=domains["healthcare"].id,
                title="Healthcare Blog",
                content="healthcare content",
                status=PublishStatus.PUBLISHED,
            ),
            Blog(
                domain_id=domains["fintech"].id,
                title="Fintech Blog",
                content="fintech content",
                status=PublishStatus.PUBLISHED,
            ),
        ]
    )
    db_session.commit()

    token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    resp = client.get("/api/team/blog", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["title"] == "Healthcare Blog"


def test_domain_can_only_have_one_blog(client, admin_user, domains):
    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    payload = {
        "domain_id": domains["healthcare"].id,
        "title": "First",
        "content": "content",
        "status": "draft",
    }
    resp = client.post("/api/admin/blogs", headers=auth_headers(admin_token), json=payload)
    assert resp.status_code == 200

    resp = client.post(
        "/api/admin/blogs",
        headers=auth_headers(admin_token),
        json={**payload, "title": "Second"},
    )
    assert resp.status_code == 409
