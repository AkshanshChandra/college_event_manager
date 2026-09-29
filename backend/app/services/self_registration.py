from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Domain, Registration
from app.models.enums import DomainStatus, PaymentMethod, PaymentStatus, RegistrationSource
from app.schemas.registration_form import RegistrationFormRequest
from app.services.registration_sync import sync_registrations_to_sheet_safe

settings = get_settings()

PENDING_PAYMENT_KEY_PREFIX = "registrations/pending-payment/"


def is_team_name_available(db: Session, team_name: str) -> bool:
    existing = (
        db.query(Registration)
        .filter(Registration.team_name.ilike(team_name.strip()))
        .one_or_none()
    )
    return existing is None


def create_self_registration(db: Session, payload: RegistrationFormRequest) -> Registration:
    """Creates the registration row — the only entry point for one, atomically
    including its payment outcome. Nothing is persisted for an incomplete
    signup: online payments must already carry an uploaded screenshot, and
    cash payments are recorded as pending-collection right away, so there's
    never a row sitting around for someone who filled the form but abandoned
    the payment step.
    """
    domain = (
        db.query(Domain)
        .filter(Domain.slug == payload.domain_slug, Domain.status == DomainStatus.ACTIVE)
        .one_or_none()
    )
    if domain is None:
        raise HTTPException(status_code=400, detail="Please choose a valid competition domain.")

    if not is_team_name_available(db, payload.team_name):
        raise HTTPException(
            status_code=409, detail="This team name is already taken. Please choose another."
        )

    email = payload.email.strip().lower()
    if db.query(Registration).filter(Registration.leader_email == email).one_or_none():
        raise HTTPException(
            status_code=409, detail="A team has already registered with this email address."
        )

    payment_method = PaymentMethod(payload.payment_method)
    now = datetime.now(timezone.utc)

    registration = Registration(
        team_name=payload.team_name.strip(),
        leader_name=payload.full_name.strip(),
        leader_email=email,
        leader_phone=payload.mobile_number.strip(),
        college=payload.college_name.strip(),
        degree_course=payload.degree_course.strip(),
        domain_slug=domain.slug,
        team_size=payload.team_size,
        members_raw=[{"name": m.name.strip(), "phone": m.phone.strip()} for m in payload.members],
        registered_at=now,
        source=RegistrationSource.MANUAL,
        raw_row=payload.model_dump(mode="json"),
        synced_at=now,
        payment_amount_inr=payload.team_size * settings.PAYMENT_PER_PERSON_INR,
        payment_method=payment_method,
    )

    if payment_method == PaymentMethod.ONLINE:
        screenshot = payload.payment_screenshot
        validate_payment_screenshot_or_raise(screenshot.original_filename, screenshot.file_size_bytes)
        if not screenshot.storage_key.startswith(PENDING_PAYMENT_KEY_PREFIX):
            raise HTTPException(status_code=400, detail="Invalid payment screenshot upload.")
        registration.payment_screenshot_key = screenshot.storage_key
        registration.payment_screenshot_filename = screenshot.original_filename
        registration.payment_screenshot_uploaded_at = now
        registration.payment_status = PaymentStatus.SUBMITTED
    else:
        # Cash: nothing to review yet — an admin marks it paid once the cash
        # is physically collected, same as verifying an online screenshot.
        registration.payment_status = PaymentStatus.PENDING

    db.add(registration)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This team name or email was just registered by someone else. Please try again.",
        )
    db.refresh(registration)
    sync_registrations_to_sheet_safe(db)
    return registration


def validate_payment_screenshot_or_raise(filename: str, file_size_bytes: int) -> None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed = settings.payment_screenshot_allowed_extensions_list
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"This file type is not supported. Allowed: {', '.join(allowed)}.",
        )
    max_bytes = settings.PAYMENT_SCREENSHOT_MAX_SIZE_MB * 1024 * 1024
    if file_size_bytes > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"The selected file exceeds the allowed size of {settings.PAYMENT_SCREENSHOT_MAX_SIZE_MB}MB.",
        )
