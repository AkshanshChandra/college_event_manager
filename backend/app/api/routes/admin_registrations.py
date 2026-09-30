import csv
import io
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.config import get_settings
from app.database import get_db
from app.models import Domain, Registration, Submission, Team, TeamMember, User
from app.models.enums import AccountStatus, DomainStatus, PaymentMethod, PaymentStatus
from app.schemas.admin import (
    PaymentStatusUpdate,
    RegistrationListItemOut,
    RegistrationUpdateRequest,
    SheetSyncResultOut,
)
from app.schemas.submission import SubmissionOut
from app.schemas.team import TeamMemberOut, TeamOut
from app.services.accounts import request_portal_access
from app.services.audit import log_action
from app.services.registration_sync import (
    MAX_TEAM_SIZE,
    member_name_and_phone,
    sync_registrations_to_sheet,
    sync_registrations_to_sheet_safe,
)
from app.services.storage import get_storage

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger("adappt.admin")
settings = get_settings()


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
        leader_phone=r.leader_phone,
        college=r.college,
        degree_course=r.degree_course,
        domain_slug=r.domain_slug,
        team_size=r.team_size,
        members=[
            {"name": name, "phone": phone}
            for name, phone in (member_name_and_phone(m) for m in r.members_raw)
        ],
        payment_status=r.payment_status.value,
        payment_method=r.payment_method.value,
        payment_amount_inr=r.payment_amount_inr,
        payment_screenshot_url=screenshot_url,
        registered_at=r.registered_at,
        account_status=_account_status_for(db, r.leader_email),
    )


@router.get("/registrations", response_model=list[RegistrationListItemOut])
def list_registrations(
    search: str | None = None,
    domain: str | None = None,
    payment_method: str | None = None,
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
    if payment_method:
        try:
            query = query.filter(Registration.payment_method == PaymentMethod(payment_method))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payment method.")

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

    sync_registrations_to_sheet_safe(db)
    return _registration_to_out(db, registration)


@router.put("/registrations/{registration_id}", response_model=RegistrationListItemOut)
def update_registration_details(
    registration_id: int,
    payload: RegistrationUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RegistrationListItemOut:
    """Lets an admin fix mistakes a participant made at registration time —
    most commonly a typo'd email address that never received the activation
    link. Keeps an already-created Team/TeamMember/User account (if any) in
    sync with the correction, so nothing is left stale.
    """
    registration = db.get(Registration, registration_id)
    if registration is None:
        raise HTTPException(status_code=404, detail="Registration not found.")

    domain = (
        db.query(Domain)
        .filter(Domain.slug == payload.domain_slug, Domain.status == DomainStatus.ACTIVE)
        .one_or_none()
    )
    if domain is None:
        raise HTTPException(status_code=400, detail="Please choose a valid competition domain.")

    new_team_name = payload.team_name.strip()
    name_conflict = (
        db.query(Registration)
        .filter(Registration.team_name.ilike(new_team_name), Registration.id != registration_id)
        .one_or_none()
    )
    if name_conflict is not None:
        raise HTTPException(status_code=409, detail="This team name is already used by another registration.")

    new_email = payload.leader_email.strip().lower()
    old_email = registration.leader_email
    if new_email != old_email:
        email_conflict = (
            db.query(Registration)
            .filter(Registration.leader_email == new_email, Registration.id != registration_id)
            .one_or_none()
        )
        if email_conflict is not None:
            raise HTTPException(status_code=409, detail="This email is already used by another registration.")

    registration.team_name = new_team_name
    registration.leader_name = payload.leader_name.strip()
    registration.leader_email = new_email
    registration.leader_phone = payload.leader_phone.strip()
    registration.college = payload.college.strip()
    registration.degree_course = payload.degree_course.strip()
    registration.domain_slug = domain.slug
    registration.team_size = payload.team_size
    registration.members_raw = [{"name": m.name.strip(), "phone": m.phone.strip()} for m in payload.members]
    registration.payment_amount_inr = payload.team_size * settings.PAYMENT_PER_PERSON_INR

    # An account/team may already exist (payment already verified) — keep it
    # in sync rather than leaving it pointing at the old details.
    team = db.query(Team).filter(Team.registration_id == registration_id).one_or_none()
    if team is not None:
        team.name = registration.team_name
        team.college = registration.college
        team.domain_id = domain.id
        for member in list(team.members):
            db.delete(member)
        for m in payload.members:
            db.add(TeamMember(team_id=team.id, name=m.name.strip(), phone=m.phone.strip()))

    if new_email != old_email:
        user = db.query(User).filter(User.email == old_email).one_or_none()
        if user is not None:
            if db.query(User).filter(User.email == new_email).one_or_none() is not None:
                raise HTTPException(status_code=409, detail="Another account already uses this email.")
            user.email = new_email

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not save changes — a conflicting registration exists.")
    db.refresh(registration)
    log_action(db, admin, "update_registration", "registration", registration.id, {"team_name": registration.team_name})
    sync_registrations_to_sheet_safe(db)
    return _registration_to_out(db, registration)


@router.post("/registrations/{registration_id}/resend-email", status_code=204)
def resend_registration_email(
    registration_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> None:
    """Re-sends the portal activation email — for when the original address
    bounced or was typo'd and has just been corrected via the edit action.
    Creates the account/team first if one doesn't exist yet.
    """
    registration = db.get(Registration, registration_id)
    if registration is None:
        raise HTTPException(status_code=404, detail="Registration not found.")

    request_portal_access(db, registration.leader_email, require_paid=False)
    log_action(db, admin, "resend_portal_credentials", "registration", registration.id)


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

    member_headers = []
    for i in range(2, MAX_TEAM_SIZE + 1):
        member_headers += [f"Member {i} Name", f"Member {i} Phone"]

    writer.writerow(
        ["Registration ID", "Team Name", "Leader Name", "Leader Email", "Leader Phone",
         "College", "Degree Course", "Domain", "Team Size"]
        + member_headers
        + ["Payment Method", "Payment Status", "Payment Amount (INR)", "Payment Screenshot",
           "Payment Screenshot Uploaded At", "Registered At", "Account Status"]
    )
    for r in rows:
        member_cells = []
        for i in range(MAX_TEAM_SIZE - 1):
            if i < len(r.members_raw):
                name, phone = member_name_and_phone(r.members_raw[i])
            else:
                name, phone = "", ""
            member_cells += [name, phone]

        writer.writerow(
            [r.id, r.team_name, r.leader_name, r.leader_email, r.leader_phone, r.college,
             r.degree_course or "", r.domain_slug, r.team_size or ""]
            + member_cells
            + [r.payment_method.value, r.payment_status.value, r.payment_amount_inr or "",
               r.payment_screenshot_filename or "Not uploaded",
               r.payment_screenshot_uploaded_at.isoformat() if r.payment_screenshot_uploaded_at else "",
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
