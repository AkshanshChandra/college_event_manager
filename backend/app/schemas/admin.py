from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.registration_form import MAX_TEAM_SIZE, MIN_TEAM_SIZE
from app.schemas.validators import validate_10_digit_phone


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
    leader_phone: str
    college: str
    degree_course: str | None
    domain_slug: str
    team_size: int | None
    members: list[dict[str, str]]
    payment_status: str
    payment_method: str
    payment_amount_inr: int | None
    payment_screenshot_url: str | None
    registered_at: datetime
    account_status: str

    model_config = {"from_attributes": True}


class PaymentStatusUpdate(BaseModel):
    payment_status: str


class RegistrationMemberEdit(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=32)

    @field_validator("phone")
    @classmethod
    def phone_is_10_digits(cls, value: str) -> str:
        return validate_10_digit_phone(value)


class RegistrationUpdateRequest(BaseModel):
    team_name: str = Field(min_length=1, max_length=255)
    leader_name: str = Field(min_length=1, max_length=255)
    leader_email: EmailStr
    leader_phone: str = Field(min_length=1, max_length=32)
    college: str = Field(min_length=1, max_length=255)
    degree_course: str = Field(min_length=1, max_length=255)
    domain_slug: str = Field(min_length=1, max_length=64)
    team_size: int = Field(ge=MIN_TEAM_SIZE, le=MAX_TEAM_SIZE)
    members: list[RegistrationMemberEdit] = Field(default_factory=list)

    @field_validator("leader_phone")
    @classmethod
    def leader_phone_is_10_digits(cls, value: str) -> str:
        return validate_10_digit_phone(value)

    @field_validator("members")
    @classmethod
    def members_match_team_size(
        cls, members: list[RegistrationMemberEdit], info
    ) -> list[RegistrationMemberEdit]:
        team_size = info.data.get("team_size")
        if team_size is not None and len(members) != team_size - 1:
            raise ValueError(
                f"Expected {max(team_size - 1, 0)} additional member(s) for a team of {team_size}, "
                f"got {len(members)}."
            )
        return members


class SyncResultOut(BaseModel):
    created: int
    updated: int
    skipped: list[dict]


class SheetSyncResultOut(BaseModel):
    rows_synced: int


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
