"""Development/demo seed data for ADAPPT.

Creates the real domains/problem statements/Round 1 settings (see
scripts/seed_data.py), plus dev-only extras: a demo admin account with a
well-known password, and 5 demo teams imported from
dev_data/registrations.csv.

For a production deploy, use `python -m scripts.bootstrap` instead — it
seeds only the real content, with no demo teams and no hardcoded password.

Usage:
    source venv/bin/activate
    python -m scripts.seed
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models import User
from app.models.enums import AccountStatus, UserRole
from app.services.registration_sync import sync_registrations
from scripts.seed_data import seed_domains_and_problem_statements, seed_round1_settings

ADMIN_EMAIL = "admin@adappt.dev"
ADMIN_PASSWORD = "ChangeMe123!"


def run() -> None:
    db = SessionLocal()
    try:
        seed_domains_and_problem_statements(db)
        seed_round1_settings(db)

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
