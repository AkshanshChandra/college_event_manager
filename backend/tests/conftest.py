import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

os.environ["DATABASE_URL"] = "postgresql+psycopg://localhost/adappt_test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["ENVIRONMENT"] = "test"
os.environ["EMAIL_BACKEND"] = "console"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["LOCAL_STORAGE_DIR"] = "/tmp/adappt_test_uploads"
os.environ["REGISTRATION_SYNC_MODE"] = "csv"
os.environ["REGISTRATION_CSV_PATH"] = str(BACKEND_ROOT / "tests" / "fixtures" / "registrations.csv")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

get_settings.cache_clear()
settings = get_settings()

from app.auth.security import hash_password  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import CompetitionSettings, Domain, User  # noqa: E402
from app.models.enums import AccountStatus, DomainStatus, UserRole  # noqa: E402
from app.services.registration_sync import sync_registrations  # noqa: E402
from app.utils.rate_limit import limiter  # noqa: E402

limiter.enabled = False  # rate limiting is exercised manually, not per-test

engine = create_engine(settings.DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def domains(db_session):
    healthcare = Domain(slug="healthcare", name="Healthcare", status=DomainStatus.ACTIVE)
    fintech = Domain(slug="fintech", name="Fintech", status=DomainStatus.ACTIVE)
    db_session.add_all([healthcare, fintech])
    db_session.commit()
    return {"healthcare": healthcare, "fintech": fintech}


@pytest.fixture()
def registrations_synced(db_session, domains):
    outcome = sync_registrations(db_session)
    assert outcome.created == 2
    return outcome


@pytest.fixture()
def round_settings(db_session):
    row = CompetitionSettings(
        round_key="round_1",
        round_label="Round 1",
        submission_start=datetime.now(timezone.utc) - timedelta(days=1),
        submission_end=datetime.now(timezone.utc) + timedelta(days=7),
        allow_replacement=True,
        max_document_size_mb=1,
        max_video_size_mb=1,
        allowed_document_extensions="pdf,ppt,pptx",
        allowed_video_extensions="mp4,mov,webm",
    )
    db_session.add(row)
    db_session.commit()
    return row


@pytest.fixture()
def admin_user(db_session):
    admin = User(
        email="admin@test.dev",
        hashed_password=hash_password("AdminPass123!"),
        role=UserRole.ADMIN,
        status=AccountStatus.ACTIVE,
    )
    db_session.add(admin)
    db_session.commit()
    return admin


def login(client, email, password) -> str:
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def activate_participant(client, monkeypatch, email, password) -> str:
    captured = {}

    def fake_send(to, team_name, activation_url):
        captured["url"] = activation_url

    monkeypatch.setattr("app.services.accounts.send_activation_email", fake_send)

    resp = client.post("/api/auth/request-access", json={"email": email})
    assert resp.status_code == 204, resp.text

    raw_token = captured["url"].rsplit("/", 1)[-1]
    resp = client.post("/api/auth/activate", json={"token": raw_token, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
