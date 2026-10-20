from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import CompetitionSettings, Domain, QualifiedTeam
from app.models.enums import DomainStatus
from app.schemas.domain import DomainOut
from app.schemas.qualified_team import PublicResultsOut
from app.services.results import get_or_create_results_settings
from app.services.self_registration import get_or_create_registration_settings
from app.services.submissions import ROUND_1_KEY, window_status

router = APIRouter(tags=["public"])
settings = get_settings()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/domains", response_model=list[DomainOut])
def list_public_domains(db: Session = Depends(get_db)) -> list[Domain]:
    return db.query(Domain).filter(Domain.status == DomainStatus.ACTIVE).all()


@router.get("/public/timeline")
def public_timeline(db: Session = Depends(get_db)) -> dict:
    round_settings = db.query(CompetitionSettings).filter_by(round_key=ROUND_1_KEY).one_or_none()
    return {
        "payment_per_person_inr": settings.PAYMENT_PER_PERSON_INR,
        "submission_start": round_settings.submission_start if round_settings else None,
        "submission_end": round_settings.submission_end if round_settings else None,
        "submission_window_status": window_status(round_settings) if round_settings else "not_open",
        "registration_open": get_or_create_registration_settings(db).is_open,
    }


@router.get("/public/results", response_model=PublicResultsOut)
def public_results(db: Session = Depends(get_db)) -> PublicResultsOut:
    settings_row = get_or_create_results_settings(db)
    if not settings_row.is_published:
        return PublicResultsOut(is_published=False, announcement=settings_row.announcement, teams=[])

    teams = (
        db.query(QualifiedTeam)
        .join(Domain)
        .order_by(Domain.name, QualifiedTeam.order_index)
        .all()
    )
    return PublicResultsOut(is_published=True, announcement=settings_row.announcement, teams=teams)
