from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import CompetitionSettings, Domain, Registration, Submission, Team, User
from app.models.enums import SubmissionStatus
from app.schemas.admin import DashboardStatsOut, SyncResultOut
from app.services.audit import log_action
from app.services.registration_sync import sync_registrations
from app.services.submissions import ROUND_1_KEY, window_status

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=DashboardStatsOut)
def dashboard(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> DashboardStatsOut:
    total_registrations = db.query(func.count(Registration.id)).scalar() or 0

    by_domain_rows = (
        db.query(Domain.name, func.count(Registration.id))
        .join(Registration, Registration.domain_slug == Domain.slug)
        .group_by(Domain.name)
        .all()
    )
    registrations_by_domain = {name: count for name, count in by_domain_rows}

    total_teams = db.query(func.count(Team.id)).scalar() or 0
    submitted_team_ids = {
        row[0]
        for row in db.query(Submission.team_id).filter(Submission.is_active_version.is_(True)).all()
    }
    total_submissions = len(submitted_team_ids)

    round_settings = db.query(CompetitionSettings).filter_by(round_key=ROUND_1_KEY).one_or_none()
    win_status = window_status(round_settings) if round_settings else "not_open"

    late_teams = 0
    if round_settings and win_status == "closed":
        late_teams = total_teams - total_submissions

    return DashboardStatsOut(
        total_registrations=total_registrations,
        registrations_by_domain=registrations_by_domain,
        total_submissions=total_submissions,
        pending_teams=max(total_teams - total_submissions - late_teams, 0),
        submitted_teams=total_submissions,
        late_teams=late_teams,
        submission_window_status=win_status,
        submission_end=round_settings.submission_end if round_settings else None,
    )


@router.post("/sync-registrations", response_model=SyncResultOut)
def sync_registrations_route(
    db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> SyncResultOut:
    outcome = sync_registrations(db)
    log_action(
        db,
        admin,
        "sync_registrations",
        "registration",
        context={"created": outcome.created, "updated": outcome.updated, "skipped": len(outcome.skipped)},
    )
    return SyncResultOut(created=outcome.created, updated=outcome.updated, skipped=outcome.skipped)
