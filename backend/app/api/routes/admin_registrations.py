import csv
import io
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import Registration, Submission, Team, User
from app.models.enums import AccountStatus, PaymentStatus
from app.schemas.admin import PaymentStatusUpdate, RegistrationListItemOut, SheetSyncResultOut
from app.schemas.submission import SubmissionOut
from app.schemas.team import TeamMemberOut, TeamOut
from app.services.accounts import request_portal_access
from app.services.audit import log_action
from app.services.registration_sync import sync_registrations_to_sheet
from app.services.storage import get_storage

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger("adappt.admin")


def _account_status_for(db: Session, email: str) -> str:
    user = db.query(User).filter(User.email == email).one_or_none()
    return user.status.value if user else "not_created"


def _registration_to_out(db: Session, r: Registration) -> RegistrationListItemOut:
    screenshot_url = None
    if r.payment_screenshot_key:
        screenshot_url = get_storage().create_presigned_download(
            r.payment_screenshot_key, r.payment_screenshot_filename or "payment-screenshot"
        )
    return RegistrationListItemOut(
        id=r.id,
        team_name=r.team_name,
        leader_name=r.leader_name,
        leader_email=r.leader_email,
        college=r.college,
        degree_course=r.degree_course,
        domain_slug=r.domain_slug,
        team_size=r.team_size,
        payment_status=r.payment_status.value,
        payment_amount_inr=r.payment_amount_inr,
        payment_screenshot_url=screenshot_url,
        registered_at=r.registered_at,
        account_status=_account_status_for(db, r.leader_email),
    )


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
    return [_registration_to_out(db, r) for r in rows]


@router.put("/registrations/{registration_id}/payment-status", response_model=RegistrationListItemOut)
def update_payment_status(
    registration_id: int,
    payload: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RegistrationListItemOut:
    registration = db.get(Registration, registration_id)
    if registration is None:
        raise HTTPException(status_code=404, detail="Registration not found.")
    try:
        new_status = PaymentStatus(payload.payment_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment status.")

    registration.payment_status = new_status
    db.commit()
    db.refresh(registration)
    log_action(
        db, admin, "update_payment_status", "registration", registration.id,
        {"payment_status": registration.payment_status.value},
    )

    if new_status == PaymentStatus.PAID:
        # Verifying payment IS what grants portal access — create the team
        # account (if needed) and send the activation email right now, so
        # the participant hears back the same day payment is confirmed
        # rather than having to separately request access afterwards.
        try:
            request_portal_access(db, registration.leader_email, require_paid=False)
            log_action(db, admin, "send_portal_credentials", "registration", registration.id)
        except Exception:
            logger.exception(
                "Payment marked paid but sending portal credentials failed for registration %s",
                registration.id,
            )

    return _registration_to_out(db, registration)


@router.post("/registrations/sync-to-sheet", response_model=SheetSyncResultOut)
def push_registrations_to_sheet(
    db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> SheetSyncResultOut:
    result = sync_registrations_to_sheet(db)
    log_action(db, admin, "push_registrations_to_sheet", "registration", context=result)
    return SheetSyncResultOut(**result)


@router.get("/registrations/export")
def export_registrations_csv(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> StreamingResponse:
    rows = db.query(Registration).order_by(Registration.registered_at.desc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["Team Name", "Leader Name", "Email", "Phone", "College", "Degree Course", "Domain",
         "Team Size", "Payment Status", "Payment Amount (INR)", "Payment Screenshot",
         "Registered At", "Account Status"]
    )
    for r in rows:
        writer.writerow(
            [r.team_name, r.leader_name, r.leader_email, r.leader_phone, r.college, r.degree_course or "",
             r.domain_slug, r.team_size or "", r.payment_status.value, r.payment_amount_inr or "",
             r.payment_screenshot_filename or "Not uploaded",
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
