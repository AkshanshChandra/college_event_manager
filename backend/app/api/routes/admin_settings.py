from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import CompetitionSettings, User
from app.schemas.admin import CompetitionSettingsOut, CompetitionSettingsUpdate
from app.services.audit import log_action
from app.services.submissions import ROUND_1_KEY

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/settings", response_model=CompetitionSettingsOut)
def get_settings_route(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> CompetitionSettings:
    row = db.query(CompetitionSettings).filter_by(round_key=ROUND_1_KEY).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Competition settings have not been configured yet.")
    return row


@router.put("/settings", response_model=CompetitionSettingsOut)
def update_settings_route(
    payload: CompetitionSettingsUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> CompetitionSettings:
    row = db.query(CompetitionSettings).filter_by(round_key=ROUND_1_KEY).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Competition settings have not been configured yet.")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    loggable_changes = {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in changes.items()}
    log_action(db, admin, "update_competition_settings", "competition_settings", row.id, loggable_changes)
    return row
