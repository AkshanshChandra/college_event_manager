from datetime import datetime, timedelta, timezone

from tests.conftest import activate_participant, auth_headers


def _publish_problem_statement(db_session, domain, title, order_index=1):
    from app.models import ProblemStatement
    from app.models.enums import PublishStatus

    ps = ProblemStatement(
        domain_id=domain.id,
        order_index=order_index,
        title=title,
        description="desc",
        status=PublishStatus.PUBLISHED,
    )
    db_session.add(ps)
    db_session.commit()
    return ps


def test_participant_only_sees_own_domain_problem_statements(
    client, db_session, domains, registrations_synced, monkeypatch
):
    _publish_problem_statement(db_session, domains["healthcare"], "Healthcare PS 1", order_index=1)
    _publish_problem_statement(db_session, domains["healthcare"], "Healthcare PS 2", order_index=2)
    _publish_problem_statement(db_session, domains["fintech"], "Fintech PS", order_index=1)

    token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    resp = client.get("/api/team/problem-statements", headers=auth_headers(token))
    assert resp.status_code == 200
    titles = [ps["title"] for ps in resp.json()]
    assert titles == ["Healthcare PS 1", "Healthcare PS 2"]


def test_unpublished_problem_statement_is_not_visible(client, db_session, domains, registrations_synced, monkeypatch):
    from app.models import ProblemStatement
    from app.models.enums import PublishStatus

    ps = ProblemStatement(
        domain_id=domains["healthcare"].id, title="Draft PS", description="d", status=PublishStatus.DRAFT
    )
    db_session.add(ps)
    db_session.commit()

    token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    resp = client.get("/api/team/problem-statements", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_hint_visibility_respects_publish_time_and_domain_scope(
    client, db_session, domains, registrations_synced, monkeypatch
):
    from app.models import Hint
    from app.models.enums import HintScope, PublishStatus

    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            Hint(
                week_number=1, title="Published global", content="c", scope=HintScope.GLOBAL,
                domain_id=None, publish_at=now - timedelta(days=1), status=PublishStatus.PUBLISHED,
            ),
            Hint(
                week_number=2, title="Future hint", content="c", scope=HintScope.GLOBAL,
                domain_id=None, publish_at=now + timedelta(days=5), status=PublishStatus.PUBLISHED,
            ),
            Hint(
                week_number=1, title="Draft hint", content="c", scope=HintScope.GLOBAL,
                domain_id=None, publish_at=now - timedelta(days=1), status=PublishStatus.DRAFT,
            ),
            Hint(
                week_number=1, title="Other domain hint", content="c", scope=HintScope.DOMAIN,
                domain_id=domains["fintech"].id, publish_at=now - timedelta(days=1), status=PublishStatus.PUBLISHED,
            ),
        ]
    )
    db_session.commit()

    token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    resp = client.get("/api/team/hints", headers=auth_headers(token))
    assert resp.status_code == 200
    titles = {h["title"] for h in resp.json()}
    assert titles == {"Published global"}


def test_admin_hint_crud_and_visibility_after_publish(client, admin_user, db_session, domains, registrations_synced, monkeypatch):
    from tests.conftest import login

    admin_token = login(client, "admin@test.dev", "AdminPass123!")
    now = datetime.now(timezone.utc)

    resp = client.post(
        "/api/admin/hints",
        headers=auth_headers(admin_token),
        json={
            "week_number": 1,
            "title": "New hint",
            "content": "content",
            "scope": "global",
            "publish_at": (now - timedelta(minutes=1)).isoformat(),
            "status": "draft",
        },
    )
    assert resp.status_code == 200
    hint_id = resp.json()["id"]

    participant_token = activate_participant(client, monkeypatch, "leader.a@example.com", "LeaderPass123!")
    resp = client.get("/api/team/hints", headers=auth_headers(participant_token))
    assert resp.json() == []

    resp = client.put(
        f"/api/admin/hints/{hint_id}", headers=auth_headers(admin_token), json={"status": "published"}
    )
    assert resp.status_code == 200

    resp = client.get("/api/team/hints", headers=auth_headers(participant_token))
    assert [h["title"] for h in resp.json()] == ["New hint"]
