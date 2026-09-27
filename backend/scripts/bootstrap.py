"""Production bootstrap for ADAPPT.

Seeds only real content: the three domains, their problem statements (see
scripts/seed_data.py), Round 1 competition settings, and one admin account
using credentials YOU supply — no demo teams, no hardcoded password, no
sample hints.

Safe to re-run: existing rows are updated in place, nothing is duplicated.

Usage:
    ADMIN_EMAIL=you@yourdomain.com ADMIN_PASSWORD='a-strong-password' \\
        python -m scripts.bootstrap
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models import User
from app.models.enums import AccountStatus, UserRole
from scripts.seed_data import seed_domains_and_problem_statements, seed_round1_settings


def run() -> None:
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        print(
            "ADMIN_EMAIL and ADMIN_PASSWORD environment variables are required.\n"
            "Example: ADMIN_EMAIL=you@yourdomain.com ADMIN_PASSWORD='...' python -m scripts.bootstrap",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if len(admin_password) < 12:
        print("ADMIN_PASSWORD should be at least 12 characters.", file=sys.stderr)
        raise SystemExit(1)

    db = SessionLocal()
    try:
        seed_domains_and_problem_statements(db)
        seed_round1_settings(db)

        admin_email = admin_email.strip().lower()
        admin = db.query(User).filter_by(email=admin_email).one_or_none()
        if admin is None:
            db.add(
                User(
                    email=admin_email,
                    hashed_password=hash_password(admin_password),
                    role=UserRole.ADMIN,
                    status=AccountStatus.ACTIVE,
                )
            )
            print(f"Created admin account: {admin_email}")
        else:
            admin.hashed_password = hash_password(admin_password)
            print(f"Updated password for existing admin account: {admin_email}")
        db.commit()

        print(
            "\nBootstrap complete. Remaining manual steps before launch:\n"
            "  - Log in as admin and review/publish the seeded problem statements.\n"
            "  - Set the real Round 1 submission_start date (Competition Settings).\n"
            "  - Add real weekly hints (none are seeded here).\n"
            "  - Configure Google Sheets sync if you want it (optional).\n"
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()
