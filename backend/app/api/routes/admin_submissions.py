from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import Submission, Team, User
from app.services.audit import log_action
from app.services.storage import get_storage

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/submissions")
def list_submissions(
    domain_slug: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[dict]:
    query = db.query(Submission).filter(Submission.is_active_version.is_(True)).join(Team)
    if domain_slug:
        query = query.join(Team.domain).filter_by(slug=domain_slug)
    if search:
        query = query.filter(Team.name.ilike(f"%{search}%"))

    results = []
    for submission in query.all():
        team = submission.team
        results.append(
            {
                "submission_id": submission.id,
                "team_id": team.id,
                "team_name": team.name,
                "domain": team.domain.name,
                "status": submission.status.value,
                "submitted_at": submission.submitted_at,
                "version": submission.version,
                "files": [
                    {"id": f.id, "file_type": f.file_type.value, "original_filename": f.original_filename}
                    for f in submission.files
                ],
            }
        )
    return results


@router.get("/submissions/{submission_id}")
def get_submission_detail(
    submission_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> dict:
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found.")

    storage = get_storage()
    return {
        "submission_id": submission.id,
        "team_name": submission.team.name,
        "version": submission.version,
        "status": submission.status.value,
        "submitted_at": submission.submitted_at,
        "files": [
            {
                "id": f.id,
                "file_type": f.file_type.value,
                "original_filename": f.original_filename,
                "file_size_bytes": f.file_size_bytes,
                "download_url": storage.create_presigned_download(f.storage_key, f.original_filename),
            }
            for f in submission.files
        ],
    }


@router.get("/submissions/{submission_id}/files/{file_id}/download-url")
def get_submission_file_download_url(
    submission_id: int, file_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> dict:
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found.")
    file = next((f for f in submission.files if f.id == file_id), None)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found.")

    storage = get_storage()
    url = storage.create_presigned_download(file.storage_key, file.original_filename)
    log_action(
        db, admin, "download_submission_file", "submission_file", file_id,
        {"team": submission.team.name, "submission_id": submission_id},
    )
    return {"download_url": url}
