from datetime import datetime

from pydantic import BaseModel, Field


class PresignRequest(BaseModel):
    file_type: str = Field(pattern="^(document|video)$")
    filename: str
    content_type: str
    file_size_bytes: int


class PresignResponse(BaseModel):
    upload_url: str
    storage_key: str
    method: str


class FileMetaIn(BaseModel):
    storage_key: str
    original_filename: str
    content_type: str
    file_size_bytes: int


class SubmitRequest(BaseModel):
    document: FileMetaIn
    video: FileMetaIn


class SubmissionFileOut(BaseModel):
    id: int
    file_type: str
    original_filename: str
    file_size_bytes: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class SubmissionOut(BaseModel):
    id: int
    version: int
    status: str
    is_active_version: bool
    submitted_at: datetime
    files: list[SubmissionFileOut]

    model_config = {"from_attributes": True}


class TeamSubmissionStateOut(BaseModel):
    window_status: str
    participant_status: str
    submission_start: datetime
    submission_end: datetime
    allow_replacement: bool
    max_document_size_mb: int
    max_video_size_mb: int
    allowed_document_extensions: list[str]
    allowed_video_extensions: list[str]
    active_submission: SubmissionOut | None
    versions: list[SubmissionOut]
