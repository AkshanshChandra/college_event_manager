import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import Registration, Submission, Team, User
from app.models.enums import AccountStatus
from app.schemas.admin import RegistrationListItemOut
from app.schemas.submission import SubmissionOut
from app.schemas.team import TeamMemberOut, TeamOut

router = APIRouter(prefix="/admin", tags=["admin"])


def _account_status_for(db: Session, email: str) -> str:
    user = db.query(User).filter(User.email == email).one_or_none()
    return user.status.value if user else "not_created"


@router.get("/registrations", response_model=list[RegistrationListItemOut])
def list_registrations(
    search: str | None = None,
    domain: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[RegistrationListItemOut]:
    query = db.query(Registration)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Registration.team_name.ilike(like))
            | (Registration.leader_name.ilike(like))
            | (Registration.leader_email.ilike(like))
            | (Registration.college.ilike(like))
        )
    if domain:
        query = query.filter(Registration.domain_slug == domain)

    rows = query.order_by(Registration.registered_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [
        RegistrationListItemOut(
            id=r.id,
            team_name=r.team_name,
            leader_name=r.leader_name,
            leader_email=r.leader_email,
            college=r.college,
            domain_slug=r.domain_slug,
            registered_at=r.registered_at,
            account_status=_account_status_for(db, r.leader_email),
        )
        for r in rows
    ]


@router.get("/registrations/export")
def export_registrations_csv(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> StreamingResponse:
    rows = db.query(Registration).order_by(Registration.registered_at.desc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Team Name", "Leader Name", "Email", "Phone", "College", "Domain", "Registered At", "Account Status"])
    for r in rows:
        writer.writerow(
            [r.team_name, r.leader_name, r.leader_email, r.leader_phone, r.college, r.domain_slug,
             r.registered_at.isoformat(), _account_status_for(db, r.leader_email)]
        )
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=adappt_registrations.csv"},
    )


@router.get("/teams", response_model=list[TeamOut])
def list_teams(
    search: str | None = None,
    domain_slug: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[TeamOut]:
    query = db.query(Team)
    if domain_slug:
        query = query.join(Team.domain).filter_by(slug=domain_slug)
    if search:
        query = query.filter(Team.name.ilike(f"%{search}%"))

    out = []
    for team in query.all():
        registration = team.registration
        out.append(
            TeamOut(
                id=team.id,
                name=team.name,
                college=team.college,
                domain=team.domain,
                members=[TeamMemberOut.model_validate(m) for m in team.members],
                leader_name=registration.leader_name,
                leader_email=registration.leader_email,
                leader_phone=registration.leader_phone,
                registered_at=registration.registered_at,
            )
        )
    return out


@router.get("/teams/{team_id}")
def get_team_detail(team_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> dict:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found.")
    registration = team.registration
    account = db.query(User).filter(User.email == registration.leader_email).one_or_none()

    return {
        "team": TeamOut(
            id=team.id,
            name=team.name,
            college=team.college,
            domain=team.domain,
            members=[TeamMemberOut.model_validate(m) for m in team.members],
            leader_name=registration.leader_name,
            leader_email=registration.leader_email,
            leader_phone=registration.leader_phone,
            registered_at=registration.registered_at,
        ),
        "account_status": account.status.value if account else "not_created",
        "submissions": [SubmissionOut.model_validate(s) for s in sorted(team.submissions, key=lambda s: s.version)],
    }
