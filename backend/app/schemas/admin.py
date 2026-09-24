from datetime import datetime

from pydantic import BaseModel


class DashboardStatsOut(BaseModel):
    total_registrations: int
    registrations_by_domain: dict[str, int]
    total_submissions: int
    pending_teams: int
    submitted_teams: int
    late_teams: int
    submission_window_status: str
    submission_end: datetime | None


class RegistrationListItemOut(BaseModel):
    id: int
    team_name: str
    leader_name: str
    leader_email: str
    college: str
    domain_slug: str
    registered_at: datetime
    account_status: str

    model_config = {"from_attributes": True}


class SyncResultOut(BaseModel):
    created: int
    updated: int
    skipped: list[dict]


class CompetitionSettingsOut(BaseModel):
    id: int
    round_key: str
    round_label: str
    submission_start: datetime
    submission_end: datetime
    allow_replacement: bool
    max_document_size_mb: int
    max_video_size_mb: int
    allowed_document_extensions: str
    allowed_video_extensions: str

    model_config = {"from_attributes": True}


class CompetitionSettingsUpdate(BaseModel):
    round_label: str | None = None
    submission_start: datetime | None = None
    submission_end: datetime | None = None
    allow_replacement: bool | None = None
    max_document_size_mb: int | None = None
    max_video_size_mb: int | None = None
    allowed_document_extensions: str | None = None
    allowed_video_extensions: str | None = None


class AuditLogOut(BaseModel):
    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: str | None
    context: dict
    created_at: datetime

    model_config = {"from_attributes": True}
