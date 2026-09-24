from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST

from app.auth.dependencies import require_participant
from app.database import get_db
from app.models import User
from app.models.enums import SubmissionFileType
from app.schemas.submission import FileMetaIn, PresignRequest, PresignResponse, SubmissionOut, SubmitRequest
from app.services.email import send_submission_confirmation_email
from app.services.storage import LocalDiskStorage, get_storage, verify_local_download_signature
from app.services.submissions import (
    FileMeta,
    assert_window_open_for_upload,
    create_new_submission_version,
    get_round_settings,
    validate_file_or_raise,
)

router = APIRouter(tags=["uploads"])


def _assert_owns_storage_key(user: User, storage_key: str) -> None:
    if not storage_key.startswith(f"teams/{user.team_id}/"):
        raise HTTPException(status_code=403, detail="You cannot access another team's files.")


@router.post("/uploads/presign", response_model=PresignResponse)
def presign_upload(
    payload: PresignRequest,
    current_user: User = Depends(require_participant),
    db: Session = Depends(get_db),
) -> PresignResponse:
    round_settings = get_round_settings(db)
    team = current_user.team
    assert_window_open_for_upload(team, round_settings)

    file_type = SubmissionFileType(payload.file_type)
    validate_file_or_raise(file_type, payload.filename, payload.file_size_bytes, round_settings)

    storage = get_storage()
    storage_key = storage.build_storage_key(team.id, payload.file_type, payload.filename)
    result = storage.create_presigned_upload(storage_key, payload.content_type)
    return PresignResponse(upload_url=result.upload_url, storage_key=result.storage_key, method=result.method)


@router.put("/uploads/local/{storage_key:path}", status_code=204)
async def local_direct_upload(
    storage_key: str,
    request: Request,
    current_user: User = Depends(require_participant),
) -> None:
    """Dev-only stand-in for an S3 presigned PUT. Only reachable when
    STORAGE_BACKEND=local; writes the request body straight to disk.
    """
    storage = get_storage()
    if not isinstance(storage, LocalDiskStorage):
        raise HTTPException(status_code=400, detail="Local upload endpoint is disabled.")
    _assert_owns_storage_key(current_user, storage_key)

    import tempfile

    dest_path = storage.resolve_path(storage_key)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        async for chunk in request.stream():
            tmp.write(chunk)
        tmp_path = tmp.name
    storage.save_local_upload(storage_key, tmp_path)


@router.get("/uploads/local-download/{storage_key:path}")
def local_direct_download(
    storage_key: str,
    filename: str,
    expires: int,
    sig: str,
) -> FileResponse:
    """Dev-only stand-in for an S3 presigned GET. The signature (embedded in
    the URL by create_presigned_download) is the credential here, exactly as
    it would be for a real presigned S3 URL — no Authorization header needed,
    so this works from a plain <a href> link.
    """
    if not verify_local_download_signature(storage_key, expires, sig):
        raise HTTPException(status_code=403, detail="This download link is invalid or has expired.")

    storage = get_storage()
    if not isinstance(storage, LocalDiskStorage):
        raise HTTPException(status_code=400, detail="Local download endpoint is disabled.")

    path = storage.resolve_path(storage_key)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(path, filename=filename)


@router.post("/submissions", response_model=SubmissionOut)
def submit_round1(
    payload: SubmitRequest,
    current_user: User = Depends(require_participant),
    db: Session = Depends(get_db),
) -> SubmissionOut:
    round_settings = get_round_settings(db)
    team = current_user.team
    assert_window_open_for_upload(team, round_settings)

    _assert_owns_storage_key(current_user, payload.document.storage_key)
    _assert_owns_storage_key(current_user, payload.video.storage_key)

    validate_file_or_raise(
        SubmissionFileType.DOCUMENT,
        payload.document.original_filename,
        payload.document.file_size_bytes,
        round_settings,
    )
    validate_file_or_raise(
        SubmissionFileType.VIDEO,
        payload.video.original_filename,
        payload.video.file_size_bytes,
        round_settings,
    )

    def to_meta(f: FileMetaIn) -> FileMeta:
        return FileMeta(
            storage_key=f.storage_key,
            original_filename=f.original_filename,
            content_type=f.content_type,
            file_size_bytes=f.file_size_bytes,
        )

    submission = create_new_submission_version(db, team, to_meta(payload.document), to_meta(payload.video))
    send_submission_confirmation_email(
        current_user.team.registration.leader_email,
        team.name,
        submission.submitted_at.isoformat(),
    )
    return submission
