"""Development/demo seed data for ADAPPT.

Creates the real domains/problem statements/Round 1 settings (see
scripts/seed_data.py), plus dev-only extras: sample weekly hints, a demo
admin account with a well-known password, and 5 demo teams imported from
dev_data/registrations.csv.

For a production deploy, use `python -m scripts.bootstrap` instead — it
seeds only the real content, with no demo teams and no hardcoded password.

Usage:
    source venv/bin/activate
    python -m scripts.seed
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models import Hint, User
from app.models.enums import AccountStatus, HintScope, PublishStatus, UserRole
from app.services.registration_sync import sync_registrations
from scripts.seed_data import seed_domains_and_problem_statements, seed_round1_settings

HINTS = [
    {
        "week_number": 1,
        "title": "[SAMPLE] Framing your problem statement",
        "content": "Focus your Week 1 effort on clearly scoping the problem before jumping into a solution.",
        "scope": HintScope.GLOBAL,
        "domain_id": None,
        "publish_at": datetime.now(timezone.utc) - timedelta(days=3),
        "status": PublishStatus.PUBLISHED,
    },
    {
        "week_number": 2,
        "title": "[SAMPLE] Validating with real users",
        "content": "Talk to at least 2 potential users of your solution before finalizing your approach.",
        "scope": HintScope.GLOBAL,
        "domain_id": None,
        "publish_at": datetime.now(timezone.utc) + timedelta(days=4),
        "status": PublishStatus.DRAFT,
    },
]

ADMIN_EMAIL = "admin@adappt.dev"
ADMIN_PASSWORD = "ChangeMe123!"


def run() -> None:
    db = SessionLocal()
    try:
        seed_domains_and_problem_statements(db)
        seed_round1_settings(db)

        for h in HINTS:
            existing = db.query(Hint).filter_by(week_number=h["week_number"], title=h["title"]).one_or_none()
            if existing is None:
                db.add(Hint(**h))
                print(f"Created hint: {h['title']}")
        db.commit()

        admin = db.query(User).filter_by(email=ADMIN_EMAIL).one_or_none()
        if admin is None:
            db.add(
                User(
                    email=ADMIN_EMAIL,
                    hashed_password=hash_password(ADMIN_PASSWORD),
                    role=UserRole.ADMIN,
                    status=AccountStatus.ACTIVE,
                )
            )
            print(f"Created admin account: {ADMIN_EMAIL} / {ADMIN_PASSWORD} (CHANGE THIS PASSWORD)")
        db.commit()

        outcome = sync_registrations(db)
        print(f"Synced registrations: {outcome.created} created, {outcome.updated} updated, "
              f"{len(outcome.skipped)} skipped.")
        for skip in outcome.skipped:
            print(f"  skipped: {skip['reason']}")

    finally:
        db.close()


if __name__ == "__main__":
    run()
