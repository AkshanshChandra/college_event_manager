from pydantic import BaseModel, EmailStr, Field, field_validator

MIN_TEAM_SIZE = 1
MAX_TEAM_SIZE = 4


def _validate_10_digit_phone(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) != 10:
        raise ValueError("Phone number must have exactly 10 digits.")
    return digits


class TeamMemberInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=32)

    @field_validator("phone")
    @classmethod
    def phone_is_10_digits(cls, value: str) -> str:
        return _validate_10_digit_phone(value)


class RegistrationFormRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    mobile_number: str = Field(min_length=1, max_length=32)
    email: EmailStr
    college_name: str = Field(min_length=1, max_length=255)
    degree_course: str = Field(min_length=1, max_length=255)
    team_name: str = Field(min_length=1, max_length=255)
    domain_slug: str = Field(min_length=1, max_length=64)
    team_size: int = Field(ge=MIN_TEAM_SIZE, le=MAX_TEAM_SIZE)
    members: list[TeamMemberInput] = Field(default_factory=list)

    @field_validator("mobile_number")
    @classmethod
    def mobile_number_is_10_digits(cls, value: str) -> str:
        return _validate_10_digit_phone(value)

    @field_validator("members")
    @classmethod
    def members_match_team_size(cls, members: list[TeamMemberInput], info) -> list[TeamMemberInput]:
        team_size = info.data.get("team_size")
        if team_size is not None and len(members) != team_size - 1:
            raise ValueError(
                f"Expected {max(team_size - 1, 0)} additional member(s) for a team of {team_size}, "
                f"got {len(members)}."
            )
        return members


class RegistrationFormResponse(BaseModel):
    registration_id: int
    team_name: str
    domain_slug: str
    team_size: int
    payment_amount_inr: int
    payment_per_person_inr: int


class TeamNameAvailabilityResponse(BaseModel):
    available: bool


class PaymentScreenshotPresignRequest(BaseModel):
    email: EmailStr
    filename: str
    content_type: str
    file_size_bytes: int


class PaymentScreenshotPresignResponse(BaseModel):
    upload_url: str
    storage_key: str
    method: str


class PaymentScreenshotConfirmRequest(BaseModel):
    email: EmailStr
    storage_key: str
    original_filename: str
    content_type: str
    file_size_bytes: int


class PaymentScreenshotConfirmResponse(BaseModel):
    registration_id: int
    payment_status: str
