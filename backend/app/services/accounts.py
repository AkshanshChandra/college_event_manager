from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.security import generate_raw_token, hash_password, hash_token
from app.config import get_settings
from app.models import ActivationToken, Registration, Team, User
from app.models.enums import AccountStatus, UserRole
from app.services.email import send_activation_email

settings = get_settings()


def request_portal_access(db: Session, email: str) -> None:
    """Look up the email in synced registration data, create the participant
    account + team if needed, and email a fresh activation link.

    Always behaves the same whether the account already existed or not, so
    this endpoint can't be used to enumerate which emails have accounts yet
    (only whether they're registered at all, which is the intended check).
    """
    email = email.strip().lower()
    registration = db.query(Registration).filter(Registration.leader_email == email).one_or_none()
    if registration is None:
        raise HTTPException(
            status_code=404,
            detail="We could not find this email in the ADAPPT registration records.",
        )

    team = registration.team
    if team is None:
        from app.models import Domain

        domain = db.query(Domain).filter(Domain.slug == registration.domain_slug).one()
        team = Team(
            name=registration.team_name,
            college=registration.college,
            domain_id=domain.id,
            registration_id=registration.id,
        )
        for member_name in registration.members_raw:
            from app.models import TeamMember

            team.members.append(TeamMember(name=member_name))
        db.add(team)
        db.flush()

    user = db.query(User).filter(User.email == email).one_or_none()
    if user is None:
        user = User(
            email=email,
            role=UserRole.PARTICIPANT,
            status=AccountStatus.PENDING_ACTIVATION,
            team_id=team.id,
        )
        db.add(user)
        db.flush()

    raw_token = generate_raw_token()
    db.add(
        ActivationToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=settings.ACTIVATION_TOKEN_EXPIRE_HOURS),
        )
    )
    db.commit()

    activation_url = f"{settings.FRONTEND_URL}/activate/{raw_token}"
    send_activation_email(email, team.name, activation_url)


def activate_account(db: Session, raw_token: str, password: str) -> User:
    token_hash = hash_token(raw_token)
    token = db.query(ActivationToken).filter(ActivationToken.token_hash == token_hash).one_or_none()

    if token is None or token.used_at is not None:
        raise HTTPException(status_code=400, detail="This activation link is invalid or has already been used.")
    if token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This activation link has expired.")

    user = token.user
    user.hashed_password = hash_password(password)
    user.status = AccountStatus.ACTIVE
    user.must_change_password = False
    token.used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user
