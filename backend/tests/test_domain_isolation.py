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
