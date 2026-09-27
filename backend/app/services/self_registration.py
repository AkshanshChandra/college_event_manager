from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Domain, Registration
from app.models.enums import DomainStatus, PaymentStatus, RegistrationSource
from app.schemas.registration_form import RegistrationFormRequest
from app.services.registration_sync import sync_registrations_to_sheet_safe

settings = get_settings()


def is_team_name_available(db: Session, team_name: str) -> bool:
    existing = (
        db.query(Registration)
        .filter(Registration.team_name.ilike(team_name.strip()))
        .one_or_none()
    )
    return existing is None


def create_self_registration(db: Session, payload: RegistrationFormRequest) -> Registration:
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

    payment_amount = payload.team_size * settings.PAYMENT_PER_PERSON_INR
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
        payment_amount_inr=payment_amount,
    )
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


def get_registration_for_email_or_raise(db: Session, registration_id: int, email: str) -> Registration:
    """Loose ownership check for the unauthenticated payment-screenshot flow:
    the participant has no portal account yet at this point (that's the
    whole point — payment isn't verified), so there's no JWT to check
    against. Knowing both the registration id and its leader email is treated
    as sufficient proof of ownership for uploading payment proof, which is
    low-stakes (worst case is a wrong image needing re-upload).
    """
    registration = db.get(Registration, registration_id)
    if registration is None or registration.leader_email != email.strip().lower():
        raise HTTPException(status_code=404, detail="Registration not found.")
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


def confirm_payment_screenshot(
    db: Session,
    registration: Registration,
    storage_key: str,
    original_filename: str,
    file_size_bytes: int,
) -> Registration:
    validate_payment_screenshot_or_raise(original_filename, file_size_bytes)

    registration.payment_screenshot_key = storage_key
    registration.payment_screenshot_filename = original_filename
    registration.payment_screenshot_uploaded_at = datetime.now(timezone.utc)
    if registration.payment_status != PaymentStatus.PAID:
        registration.payment_status = PaymentStatus.SUBMITTED
    db.commit()
    db.refresh(registration)
    sync_registrations_to_sheet_safe(db)
    return registration
