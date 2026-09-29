import time
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.registration_form import (
    PaymentScreenshotPresignRequest,
    PaymentScreenshotPresignResponse,
    RegistrationFormRequest,
    RegistrationFormResponse,
    TeamNameAvailabilityResponse,
)
from app.services.self_registration import (
    create_self_registration,
    is_team_name_available,
    validate_payment_screenshot_or_raise,
)
from app.services.storage import LocalDiskStorage, build_pending_payment_key, get_storage, sign_local_download
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
        payment_method=registration.payment_method.value,
        payment_status=registration.payment_status.value,
    )


@router.post("/payment-screenshot/presign", response_model=PaymentScreenshotPresignResponse)
@limiter.limit("20/minute")
def presign_payment_screenshot(
    request: Request, payload: PaymentScreenshotPresignRequest
) -> PaymentScreenshotPresignResponse:
    """Presigns a payment-screenshot upload before any registration exists —
    the registration is only created once this upload is confirmed (or cash
    is chosen instead), so there's no registration id to scope this to.
    """
    validate_payment_screenshot_or_raise(payload.filename, payload.file_size_bytes)

    storage = get_storage()
    storage_key = build_pending_payment_key(payload.filename)

    if isinstance(storage, LocalDiskStorage):
        # The local dev stand-in needs its own unauthenticated upload route,
        # authorized the same way a real S3 presigned PUT is: the signature
        # embedded in the URL itself is the credential, not a JWT.
        expires_at = int(time.time()) + settings.PRESIGNED_URL_EXPIRE_SECONDS
        signature = sign_local_download(storage_key, expires_at)
        upload_url = (
            f"{settings.API_PREFIX}/uploads/registration-payment/{storage_key}"
            f"?expires={expires_at}&sig={quote(signature)}"
        )
        method = "PUT"
    else:
        result = storage.create_presigned_upload(storage_key, payload.content_type)
        upload_url, method = result.upload_url, result.method

    return PaymentScreenshotPresignResponse(upload_url=upload_url, storage_key=storage_key, method=method)
