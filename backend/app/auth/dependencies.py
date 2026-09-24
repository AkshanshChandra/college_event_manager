from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_token
from app.database import get_db
from app.models import User
from app.models.enums import AccountStatus, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise CREDENTIALS_ERROR

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise CREDENTIALS_ERROR

    user_id = payload.get("sub")
    user = db.get(User, int(user_id)) if user_id else None
    if user is None:
        raise CREDENTIALS_ERROR
    if user.status != AccountStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="Account is not active.")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


def require_participant(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.PARTICIPANT:
        raise HTTPException(status_code=403, detail="Participant access required.")
    if current_user.team_id is None:
        raise HTTPException(status_code=403, detail="No team is associated with this account.")
    return current_user
