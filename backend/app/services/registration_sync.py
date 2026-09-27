"""Registration data sync.

The portal's own registration form (app/services/self_registration.py) is the
source of truth for new registrations. This module covers two optional,
separate sync directions kept for organizer convenience:

  - sync_registrations(): pulls rows IN from a CSV (local dev) or a Google
    Sheet into the `registrations` table — a legacy bulk-import path, useful
    for e.g. importing a spreadsheet of registrations collected before the
    native form existed. Chosen by settings.REGISTRATION_SYNC_MODE.
  - sync_registrations_to_sheet(): pushes the current `registrations` table
    OUT to a Google Sheet, so organizers can view/filter/share the list in a
    familiar spreadsheet.
"""

import csv
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Domain, Registration, User
from app.models.enums import RegistrationSource

settings = get_settings()
logger = logging.getLogger("adappt.registration_sync")

MAX_TEAM_SIZE = 4  # matches RegistrationFormRequest — up to 3 members beyond the leader

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
    team_names_in_use = {t.lower() for t, in db.query(Registration.team_name).all()}

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

        team_name = row["team_name"].strip()
        team_name_key = team_name.lower()
        already_taken = team_name_key in team_names_in_use and not (
            existing and existing.team_name.strip().lower() == team_name_key
        )
        if already_taken:
            outcome.skipped.append({"row": raw_row, "reason": f"team name '{team_name}' already in use"})
            continue
        team_names_in_use.add(team_name_key)

        registered_at = _parse_timestamp(row.get("timestamp"))

        if existing:
            existing.team_name = team_name
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


_MEMBER_HEADERS = [
    header
    for i in range(2, MAX_TEAM_SIZE + 1)
    for header in (f"Member {i} Name", f"Member {i} Phone")
]

SHEET_HEADERS = (
    ["Registration ID", "Team Name", "Leader Name", "Leader Email", "Leader Phone",
     "College", "Degree Course", "Domain", "Team Size"]
    + _MEMBER_HEADERS
    + ["Payment Status", "Payment Amount (INR)", "Payment Screenshot",
       "Payment Screenshot Uploaded At", "Registered At", "Account Status"]
)


def member_name_and_phone(member: dict | str) -> tuple[str, str]:
    # Legacy CSV/Sheets-imported rows store plain name strings (no phone);
    # the native registration form stores {"name": ..., "phone": ...} dicts.
    if isinstance(member, dict):
        return member.get("name", ""), member.get("phone", "")
    return str(member), ""


def _account_status_for(db: Session, email: str) -> str:
    user = db.query(User).filter(User.email == email).one_or_none()
    return user.status.value if user else "not_created"


def sync_registrations_to_sheet(db: Session) -> dict:
    """Pushes every registration to the configured Google Sheet, overwriting
    its current contents so the sheet always mirrors the database exactly —
    same columns as the admin CSV export.
    """
    from app.integrations.google_forms import push_rows_to_sheet

    registrations = db.query(Registration).order_by(Registration.registered_at.asc()).all()
    rows = []
    for r in registrations:
        member_cells = []
        for i in range(MAX_TEAM_SIZE - 1):
            if i < len(r.members_raw):
                name, phone = member_name_and_phone(r.members_raw[i])
            else:
                name, phone = "", ""
            member_cells += [name, phone]

        rows.append(
            [r.id, r.team_name, r.leader_name, r.leader_email, r.leader_phone, r.college,
             r.degree_course or "", r.domain_slug, r.team_size or ""]
            + member_cells
            + [r.payment_status.value, r.payment_amount_inr or "",
               r.payment_screenshot_filename or "Not uploaded",
               r.payment_screenshot_uploaded_at.isoformat() if r.payment_screenshot_uploaded_at else "",
               r.registered_at.isoformat(), _account_status_for(db, r.leader_email)]
        )
    push_rows_to_sheet(SHEET_HEADERS, rows)
    return {"rows_synced": len(rows)}


def sync_registrations_to_sheet_safe(db: Session) -> None:
    """Best-effort real-time push, called right after any registration
    mutation. Swallows and logs failures (Sheets not configured, transient
    Google API errors) so a sync problem never breaks the request that
    triggered it — registration, payment upload, and payment verification
    all still succeed even if the sheet push fails.
    """
    try:
        sync_registrations_to_sheet(db)
    except Exception:
        logger.exception("Real-time Google Sheets sync failed")
