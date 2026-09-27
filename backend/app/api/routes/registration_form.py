from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.registration_form import (
    PaymentScreenshotConfirmRequest,
    PaymentScreenshotConfirmResponse,
    PaymentScreenshotPresignRequest,
    PaymentScreenshotPresignResponse,
    RegistrationFormRequest,
    RegistrationFormResponse,
    TeamNameAvailabilityResponse,
)
from app.services.self_registration import (
    confirm_payment_screenshot,
    create_self_registration,
    get_registration_for_email_or_raise,
    is_team_name_available,
    validate_payment_screenshot_or_raise,
)
from app.services.storage import LocalDiskStorage, build_registration_payment_key, get_storage
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/registrations", tags=["registration"])
settings = get_settings()


@router.get("/check-team-name", response_model=TeamNameAvailabilityResponse)
def check_team_name(team_name: str, db: Session = Depends(get_db)) -> TeamNameAvailabilityResponse:
    return TeamNameAvailabilityResponse(available=is_team_name_available(db, team_name))


@router.post("", response_model=RegistrationFormResponse)
@limiter.limit("10/minute")
def submit_registration(
    request: Request, payload: RegistrationFormRequest, db: Session = Depends(get_db)
) -> RegistrationFormResponse:
    registration = create_self_registration(db, payload)
    return RegistrationFormResponse(
        registration_id=registration.id,
        team_name=registration.team_name,
        domain_slug=registration.domain_slug,
        team_size=registration.team_size,
        payment_amount_inr=registration.payment_amount_inr,
        payment_per_person_inr=settings.PAYMENT_PER_PERSON_INR,
    )


@router.post("/{registration_id}/payment-screenshot/presign", response_model=PaymentScreenshotPresignResponse)
@limiter.limit("20/minute")
def presign_payment_screenshot(
    request: Request,
    registration_id: int,
    payload: PaymentScreenshotPresignRequest,
    db: Session = Depends(get_db),
) -> PaymentScreenshotPresignResponse:
    get_registration_for_email_or_raise(db, registration_id, payload.email)
    validate_payment_screenshot_or_raise(payload.filename, payload.file_size_bytes)

    storage = get_storage()
    storage_key = build_registration_payment_key(registration_id, payload.filename)

    if isinstance(storage, LocalDiskStorage):
        # The local dev stand-in needs its own unauthenticated upload route
        # (registration-payment) rather than the team-scoped, JWT-authenticated
        # one submissions use — a real S3 presigned PUT doesn't have this
        # problem since it's routed straight to S3, not through our API. The
        # ownership check (registration_id + email) is embedded in the URL
        # itself here, exactly as it's embedded in a real presigned URL's
        # signature, so the frontend can PUT to upload_url as-is either way.
        upload_url = (
            f"{settings.API_PREFIX}/uploads/registration-payment/{storage_key}"
            f"?registration_id={registration_id}&email={quote(payload.email)}"
        )
        method = "PUT"
    else:
        result = storage.create_presigned_upload(storage_key, payload.content_type)
        upload_url, method = result.upload_url, result.method

    return PaymentScreenshotPresignResponse(upload_url=upload_url, storage_key=storage_key, method=method)


@router.post("/{registration_id}/payment-screenshot/confirm", response_model=PaymentScreenshotConfirmResponse)
@limiter.limit("20/minute")
def confirm_payment_screenshot_route(
    request: Request,
    registration_id: int,
    payload: PaymentScreenshotConfirmRequest,
    db: Session = Depends(get_db),
) -> PaymentScreenshotConfirmResponse:
    registration = get_registration_for_email_or_raise(db, registration_id, payload.email)
    expected_prefix = f"registrations/{registration_id}/payment/"
    if not payload.storage_key.startswith(expected_prefix):
        raise HTTPException(status_code=400, detail="Invalid storage key for this registration.")

    registration = confirm_payment_screenshot(
        db, registration, payload.storage_key, payload.original_filename, payload.file_size_bytes
    )
    return PaymentScreenshotConfirmResponse(
        registration_id=registration.id, payment_status=registration.payment_status.value
    )
