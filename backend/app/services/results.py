from sqlalchemy.orm import Session

from app.models import ResultsSettings


def get_or_create_results_settings(db: Session) -> ResultsSettings:
    row = db.query(ResultsSettings).first()
    if row is None:
        row = ResultsSettings(is_published=False)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row
