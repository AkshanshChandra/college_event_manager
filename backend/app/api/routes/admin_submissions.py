import os
import re
import shutil
import tempfile
import zipfile

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import Submission, Team, User
from app.schemas.submission import SubmissionsZipExportOut
from app.services.audit import log_action
from app.services.storage import get_storage

_SUBMISSIONS_EXPORT_KEY = "exports/adappt_submissions.zip"

router = APIRouter(prefix="/admin", tags=["admin"])

_UNSAFE_PATH_CHARS = re.compile(r'[\\/:*?"<>|]')


def _safe_folder_name(name: str) -> str:
    cleaned = _UNSAFE_PATH_CHARS.sub("-", name).strip()
    return cleaned or "untitled"


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


@router.get("/submissions/export-zip", response_model=SubmissionsZipExportOut)
def export_submissions_zip(
    db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> SubmissionsZipExportOut:
    """Builds every team's active Round 1 submission into one zip, organized
    as <domain>/<team>/<file>, uploads it to storage, and hands back a
    presigned download link.

    This used to stream the zip straight back as the response body, which
    the admin's browser had to buffer entirely in page memory (via
    axios's blob responseType) before it could be saved — fine at a few
    hundred MB, but once most teams had submitted (each with a video up to
    300MB) the export grew into multiple GB and that buffering step made
    the download look permanently stuck even though the server had already
    finished. A presigned link lets the browser download it natively
    instead — streamed straight to disk, with real progress and no
    in-page memory buffering.
    """
    submissions = (
        db.query(Submission).filter(Submission.is_active_version.is_(True)).join(Team).all()
    )
    if not submissions:
        raise HTTPException(status_code=404, detail="No submissions to export yet.")

    storage = get_storage()
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp.close()

    try:
        with zipfile.ZipFile(tmp.name, mode="w", compression=zipfile.ZIP_STORED) as zf:
            for submission in submissions:
                team = submission.team
                folder = f"{_safe_folder_name(team.domain.name)}/{_safe_folder_name(team.name)}"
                for f in submission.files:
                    stream = storage.open_read_stream(f.storage_key)
                    try:
                        with zf.open(f"{folder}/{f.original_filename}", mode="w") as dest:
                            shutil.copyfileobj(stream, dest, length=1024 * 1024)
                    finally:
                        stream.close()
        storage.upload_local_file(_SUBMISSIONS_EXPORT_KEY, tmp.name, "application/zip")
    except Exception:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
        raise

    log_action(db, admin, "export_submissions_zip", "submission", context={"count": len(submissions)})

    download_url = storage.create_presigned_download(_SUBMISSIONS_EXPORT_KEY, "adappt_submissions.zip")
    return SubmissionsZipExportOut(download_url=download_url)


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
