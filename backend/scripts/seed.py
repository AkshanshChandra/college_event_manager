"""Development/demo seed data for ADAPPT.

Creates: an admin account, three sample domains with problem statements,
sample weekly hints, Round 1 settings, and syncs the bundled dev registration
CSV. Everything here is clearly demo data — replace before going live.

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
from app.models import CompetitionSettings, Domain, Hint, ProblemStatement, User
from app.models.enums import AccountStatus, DomainStatus, HintScope, PublishStatus, UserRole
from app.services.registration_sync import sync_registrations

DOMAINS = [
    {
        "slug": "healthcare",
        "name": "Healthcare",
        "description": "Technology solutions that improve patient outcomes, care access, or clinical workflows.",
    },
    {
        "slug": "fintech",
        "name": "Fintech",
        "description": "Solutions that make financial services more inclusive, secure, or efficient.",
    },
    {
        "slug": "sustainability",
        "name": "Sustainability",
        "description": "Solutions that reduce environmental impact or support sustainable resource use.",
    },
]

PROBLEM_STATEMENTS = {
    "healthcare": {
        "title": "[SAMPLE] Early Warning System for Rural Patient Deterioration",
        "description": (
            "Design a solution that helps rural primary health centers detect early signs of "
            "patient deterioration using low-cost, low-connectivity monitoring."
        ),
        "requirements": "Must work with intermittent connectivity. Must support multilingual UI.",
        "constraints": "No dependency on specialist hardware costing more than ₹5,000/unit.",
        "deliverables": "Working prototype, architecture document, 5-minute demo video.",
    },
    "fintech": {
        "title": "[SAMPLE] Micro-Credit Risk Scoring for Gig Workers",
        "description": (
            "Build a credit-scoring approach for gig economy workers who lack traditional "
            "credit history, using alternative data sources."
        ),
        "requirements": "Must explain scoring decisions. Must not use protected demographic attributes.",
        "constraints": "Solution must be explainable to a non-technical loan officer.",
        "deliverables": "Working prototype, model/approach writeup, 5-minute demo video.",
    },
    "sustainability": {
        "title": "[SAMPLE] Hyperlocal Waste Segregation Incentive Platform",
        "description": (
            "Design a platform that increases household waste segregation compliance in "
            "urban neighborhoods through incentives and feedback."
        ),
        "requirements": "Must work on entry-level Android devices. Must support offline data capture.",
        "constraints": "No reliance on paid third-party SMS gateways.",
        "deliverables": "Working prototype, impact model, 5-minute demo video.",
    },
}

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
        domains_by_slug = {}
        for d in DOMAINS:
            domain = db.query(Domain).filter_by(slug=d["slug"]).one_or_none()
            if domain is None:
                domain = Domain(status=DomainStatus.ACTIVE, **d)
                db.add(domain)
                db.flush()
                print(f"Created domain: {domain.name}")
            domains_by_slug[d["slug"]] = domain
        db.commit()

        for slug, ps_data in PROBLEM_STATEMENTS.items():
            domain = domains_by_slug[slug]
            existing = db.query(ProblemStatement).filter_by(domain_id=domain.id).one_or_none()
            if existing is None:
                db.add(ProblemStatement(domain_id=domain.id, status=PublishStatus.PUBLISHED, **ps_data))
                print(f"Created problem statement for: {domain.name}")
        db.commit()

        for h in HINTS:
            existing = db.query(Hint).filter_by(week_number=h["week_number"], title=h["title"]).one_or_none()
            if existing is None:
                db.add(Hint(**h))
                print(f"Created hint: {h['title']}")
        db.commit()

        settings_row = db.query(CompetitionSettings).filter_by(round_key="round_1").one_or_none()
        if settings_row is None:
            db.add(
                CompetitionSettings(
                    round_key="round_1",
                    round_label="Round 1",
                    submission_start=datetime.now(timezone.utc) - timedelta(days=1),
                    submission_end=datetime.now(timezone.utc) + timedelta(days=14),
                    allow_replacement=True,
                    max_document_size_mb=25,
                    max_video_size_mb=300,
                    allowed_document_extensions="pdf,ppt,pptx",
                    allowed_video_extensions="mp4,mov,webm",
                )
            )
            print("Created Round 1 competition settings.")
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
