"""Synchronizes registration data (Google Form responses) into the
`registrations` table, which is the source of truth for "is this email
actually registered". Two sources are supported, chosen by
settings.REGISTRATION_SYNC_MODE:

  - "csv": reads a local CSV shaped like the Google Form response sheet.
    Used for local development before real Google credentials exist.
  - "google_sheets": reads live via app.integrations.google_forms.

Either way, rows funnel through the same validation/dedup/normalization path
so switching sources later requires no changes to the sync semantics.
"""

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Domain, Registration
from app.models.enums import RegistrationSource

settings = get_settings()

REQUIRED_FIELDS = ("team_name", "leader_name", "leader_email", "leader_phone", "college", "domain")

# Maps a variety of plausible Google Form column headers to our canonical field names.
HEADER_ALIASES = {
    "team_name": {"team name", "team_name", "teamname"},
    "leader_name": {"team leader name", "leader name", "leader_name", "team leader"},
    "leader_email": {"team leader email", "leader email", "email", "leader_email"},
    "leader_phone": {"phone", "contact", "phone/contact", "leader_phone", "team leader phone"},
    "college": {"college", "institution", "college/university"},
    "domain": {"domain", "competition domain", "chosen domain"},
    "members": {"team members", "members", "member names"},
    "timestamp": {"timestamp", "registration timestamp", "registered_at"},
}


@dataclass
class SyncOutcome:
    created: int = 0
    updated: int = 0
    skipped: list[dict] = field(default_factory=list)  # [{row, reason}]


def _normalize_headers(row: dict) -> dict:
    normalized = {}
    lower_row = {k.strip().lower(): v for k, v in row.items()}
    for canonical, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            if alias in lower_row:
                normalized[canonical] = lower_row[alias]
                break
    return normalized


def _split_members(raw: str | None) -> list[str]:
    if not raw:
        return []
    for sep in (";", "|", ","):
        if sep in raw:
            return [m.strip() for m in raw.split(sep) if m.strip()]
    return [raw.strip()] if raw.strip() else []


def _read_csv_rows(csv_path: str) -> list[dict]:
    path = Path(csv_path)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _fetch_raw_rows() -> list[dict]:
    if settings.REGISTRATION_SYNC_MODE == "google_sheets":
        from app.integrations.google_forms import fetch_registration_rows

        return fetch_registration_rows()
    return _read_csv_rows(settings.REGISTRATION_CSV_PATH)


def sync_registrations(db: Session) -> SyncOutcome:
    outcome = SyncOutcome()
    domains_by_name = {d.name.strip().lower(): d for d in db.query(Domain).all()}
    domains_by_slug = {d.slug: d for d in db.query(Domain).all()}

    source = (
        RegistrationSource.GOOGLE_SHEETS
        if settings.REGISTRATION_SYNC_MODE == "google_sheets"
        else RegistrationSource.CSV
    )

    for raw_row in _fetch_raw_rows():
        row = _normalize_headers(raw_row)

        missing = [f for f in REQUIRED_FIELDS if not row.get(f)]
        if missing:
            outcome.skipped.append({"row": raw_row, "reason": f"missing fields: {missing}"})
            continue

        domain_key = row["domain"].strip().lower()
        domain = domains_by_name.get(domain_key) or domains_by_slug.get(domain_key)
        if domain is None:
            outcome.skipped.append(
                {"row": raw_row, "reason": f"unknown domain '{row['domain']}'"}
            )
            continue

        email = row["leader_email"].strip().lower()
        existing = (
            db.query(Registration).filter(Registration.leader_email == email).one_or_none()
        )

        registered_at = _parse_timestamp(row.get("timestamp"))

        if existing:
            existing.team_name = row["team_name"].strip()
            existing.leader_name = row["leader_name"].strip()
            existing.leader_phone = row["leader_phone"].strip()
            existing.college = row["college"].strip()
            existing.domain_slug = domain.slug
            existing.members_raw = _split_members(row.get("members"))
            existing.raw_row = raw_row
            existing.synced_at = datetime.now(timezone.utc)
            outcome.updated += 1
        else:
            db.add(
                Registration(
                    team_name=row["team_name"].strip(),
                    leader_name=row["leader_name"].strip(),
                    leader_email=email,
                    leader_phone=row["leader_phone"].strip(),
                    college=row["college"].strip(),
                    domain_slug=domain.slug,
                    members_raw=_split_members(row.get("members")),
                    registered_at=registered_at,
                    source=source,
                    raw_row=raw_row,
                    synced_at=datetime.now(timezone.utc),
                )
            )
            outcome.created += 1

    db.commit()
    return outcome


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)
