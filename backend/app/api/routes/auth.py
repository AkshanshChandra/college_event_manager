from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.database import get_db
from app.models import User
from app.models.enums import AccountStatus
from app.schemas.auth import (
    ActivateRequest,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    RequestAccessRequest,
    TokenResponse,
)
from app.services.accounts import activate_account, request_portal_access
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request-access", status_code=204)
@limiter.limit("5/minute")
def request_access(request: Request, payload: RequestAccessRequest, db: Session = Depends(get_db)) -> None:
    request_portal_access(db, payload.email)


@router.post("/activate", response_model=TokenResponse)
def activate(payload: ActivateRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = activate_account(db, payload.token, payload.password)
    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id), user.role.value),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email.lower()).one_or_none()
    if user is None or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if user.status != AccountStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="This account is not active yet.")

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id), user.role.value),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    data = decode_token(payload.refresh_token)
    if data is None or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    user = db.get(User, int(data["sub"]))
    if user is None or user.status != AccountStatus.ACTIVE:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id), user.role.value),
    )


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
