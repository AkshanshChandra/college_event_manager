import enum

from sqlalchemy import Enum as SAEnum


def pg_enum(enum_cls: type[enum.Enum], name: str | None = None) -> SAEnum:
    """SQLAlchemy Enum that persists the member's .value (lowercase) as the
    Postgres enum label, instead of the default behavior of persisting .name.
    """
    return SAEnum(
        enum_cls,
        name=name or enum_cls.__name__.lower(),
        values_callable=lambda cls: [member.value for member in cls],
    )


class UserRole(str, enum.Enum):
    PARTICIPANT = "participant"
    ADMIN = "admin"


class AccountStatus(str, enum.Enum):
    PENDING_ACTIVATION = "pending_activation"
    ACTIVE = "active"
    DISABLED = "disabled"


class DomainStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PublishStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    LATE = "late"


class SubmissionFileType(str, enum.Enum):
    DOCUMENT = "document"
    VIDEO = "video"


class RegistrationSource(str, enum.Enum):
    CSV = "csv"
    GOOGLE_SHEETS = "google_sheets"
    MANUAL = "manual"


class HintScope(str, enum.Enum):
    GLOBAL = "global"
    DOMAIN = "domain"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"  # registered, no payment proof uploaded yet
    SUBMITTED = "submitted"  # payment screenshot uploaded, awaiting admin verification
    PAID = "paid"  # admin has verified the payment screenshot
