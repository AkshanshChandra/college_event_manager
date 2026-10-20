from tests.conftest import auth_headers, login


def test_results_hidden_until_published(client, admin_user, domains):
    admin_token = login(client, "admin@test.dev", "AdminPass123!")

    resp = client.post(
        "/api/admin/qualified-teams",
        headers=auth_headers(admin_token),
        json={"domain_id": domains["healthcare"].id, "team_name": "Team Alpha", "college": "MPSTME", "order_index": 1},
    )
    assert resp.status_code == 200, resp.text
    team_id = resp.json()["id"]

    # Not published yet — public endpoint hides the list entirely.
    resp = client.get("/api/public/results")
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_published"] is False
    assert body["teams"] == []

    resp = client.put(
        "/api/admin/results-settings",
        headers=auth_headers(admin_token),
        json={"is_published": True, "announcement": "Congratulations to all qualifying teams!"},
    )
    assert resp.status_code == 200, resp.text

    resp = client.get("/api/public/results")
    body = resp.json()
    assert body["is_published"] is True
    assert body["announcement"] == "Congratulations to all qualifying teams!"
    assert len(body["teams"]) == 1
    assert body["teams"][0]["team_name"] == "Team Alpha"
    assert body["teams"][0]["college"] == "MPSTME"
    assert body["teams"][0]["domain"]["slug"] == domains["healthcare"].slug

    # Clean-up path: delete it and confirm it disappears.
    resp = client.delete(f"/api/admin/qualified-teams/{team_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 204
    resp = client.get("/api/public/results")
    assert resp.json()["teams"] == []


def test_results_grouped_and_ordered(client, admin_user, domains):
    admin_token = login(client, "admin@test.dev", "AdminPass123!")

    for name, domain_key, order in [
        ("Team B", "fintech", 2),
        ("Team A", "fintech", 1),
        ("Team Z", "healthcare", 1),
    ]:
        resp = client.post(
            "/api/admin/qualified-teams",
            headers=auth_headers(admin_token),
            json={"domain_id": domains[domain_key].id, "team_name": name, "order_index": order},
        )
        assert resp.status_code == 200, resp.text

    client.put("/api/admin/results-settings", headers=auth_headers(admin_token), json={"is_published": True})

    resp = client.get("/api/public/results")
    names_in_order = [t["team_name"] for t in resp.json()["teams"]]
    # Domains alphabetically (Fintech, Healthcare), order_index within each.
    assert names_in_order == ["Team A", "Team B", "Team Z"]


def test_admin_can_update_and_reject_invalid_domain(client, admin_user, domains):
    admin_token = login(client, "admin@test.dev", "AdminPass123!")

    resp = client.post(
        "/api/admin/qualified-teams",
        headers=auth_headers(admin_token),
        json={"domain_id": domains["healthcare"].id, "team_name": "Team Alpha"},
    )
    team_id = resp.json()["id"]

    resp = client.put(
        f"/api/admin/qualified-teams/{team_id}",
        headers=auth_headers(admin_token),
        json={"team_name": "Team Alpha Renamed"},
    )
    assert resp.status_code == 200
    assert resp.json()["team_name"] == "Team Alpha Renamed"

    resp = client.post(
        "/api/admin/qualified-teams",
        headers=auth_headers(admin_token),
        json={"domain_id": 999999, "team_name": "Ghost Team"},
    )
    assert resp.status_code == 400
