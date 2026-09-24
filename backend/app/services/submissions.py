from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import CompetitionSettings, Submission, SubmissionFile, Team
from app.models.enums import SubmissionFileType, SubmissionStatus

settings = get_settings()

ROUND_1_KEY = "round_1"


@dataclass
class FileMeta:
    storage_key: str
    original_filename: str
    content_type: str
    file_size_bytes: int


def get_round_settings(db: Session, round_key: str = ROUND_1_KEY) -> CompetitionSettings:
    row = db.query(CompetitionSettings).filter_by(round_key=round_key).one_or_none()
    if row is None:
        raise HTTPException(
            status_code=500,
            detail="Competition settings are not configured. An admin must configure them first.",
        )
    return row


def window_status(round_settings: CompetitionSettings, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    if now < round_settings.submission_start:
        return "not_open"
    if now > round_settings.submission_end:
        return "closed"
    return "open"


def participant_submission_status(
    team: Team, round_settings: CompetitionSettings, now: datetime | None = None
) -> str:
    now = now or datetime.now(timezone.utc)
    active = next((s for s in team.submissions if s.is_active_version), None)
    if active:
        return active.status.value
    if now > round_settings.submission_end:
        return "late"
    return "pending"


def validate_file_or_raise(
    file_type: SubmissionFileType, filename: str, file_size_bytes: int, round_settings: CompetitionSettings
) -> None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if file_type == SubmissionFileType.DOCUMENT:
        allowed = [e.strip().lower() for e in round_settings.allowed_document_extensions.split(",")]
        max_mb = round_settings.max_document_size_mb
    else:
        allowed = [e.strip().lower() for e in round_settings.allowed_video_extensions.split(",")]
        max_mb = round_settings.max_video_size_mb

    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"This file type is not supported. Allowed: {', '.join(allowed)}.",
        )
    if file_size_bytes > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"The selected file exceeds the allowed size of {max_mb}MB.",
        )


def assert_window_open_for_upload(team: Team, round_settings: CompetitionSettings) -> None:
    status = window_status(round_settings)
    if status == "not_open":
        raise HTTPException(status_code=403, detail="Round 1 submissions are not open yet.")
    if status == "closed":
        raise HTTPException(status_code=403, detail="Round 1 submissions are currently closed.")

    has_existing = any(s.is_active_version for s in team.submissions)
    if has_existing and not round_settings.allow_replacement:
        raise HTTPException(
            status_code=403, detail="Submission replacement is not allowed for this round."
        )


def create_new_submission_version(
    db: Session, team: Team, document: FileMeta, video: FileMeta
) -> Submission:
    now = datetime.now(timezone.utc)
    for existing in team.submissions:
        existing.is_active_version = False

    next_version = max((s.version for s in team.submissions), default=0) + 1

    submission = Submission(
        team_id=team.id,
        version=next_version,
        status=SubmissionStatus.SUBMITTED,
        is_active_version=True,
        submitted_at=now,
    )
    submission.files = [
        SubmissionFile(
            file_type=SubmissionFileType.DOCUMENT,
            original_filename=document.original_filename,
            storage_key=document.storage_key,
            content_type=document.content_type,
            file_size_bytes=document.file_size_bytes,
            uploaded_at=now,
        ),
        SubmissionFile(
            file_type=SubmissionFileType.VIDEO,
            original_filename=video.original_filename,
            storage_key=video.storage_key,
            content_type=video.content_type,
            file_size_bytes=video.file_size_bytes,
            uploaded_at=now,
        ),
    ]
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission
