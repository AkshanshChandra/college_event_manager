from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import CompetitionSettings, Domain
from app.models.enums import DomainStatus
from app.schemas.domain import DomainOut
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
        "google_form_url": settings.GOOGLE_FORM_URL,
        "submission_start": round_settings.submission_start if round_settings else None,
        "submission_end": round_settings.submission_end if round_settings else None,
        "submission_window_status": window_status(round_settings) if round_settings else "not_open",
    }
