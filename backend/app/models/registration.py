from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import PaymentStatus, RegistrationSource, pg_enum
from app.models.mixins import TimestampMixin


class Registration(Base, TimestampMixin):
    """A registered team, either submitted through the portal's own
    registration form (source=MANUAL) or imported from a CSV / Google Sheet
    (source=CSV / GOOGLE_SHEETS, for bulk-import scenarios).

    This is the source of truth for "did this email actually register".
    A Team/User is only ever created from a row that exists here.
    """

    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    leader_name: Mapped[str] = mapped_column(String(255))
    leader_email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    leader_phone: Mapped[str] = mapped_column(String(32))
    college: Mapped[str] = mapped_column(String(255))
    degree_course: Mapped[str | None] = mapped_column(String(255), nullable=True)
    domain_slug: Mapped[str] = mapped_column(String(64))
    team_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Legacy CSV/Sheets rows store a list of member name strings; the native
    # registration form stores a list of {"name": ..., "phone": ...} dicts
    # for every member beyond the leader.
    members_raw: Mapped[list] = mapped_column(JSON, default=list)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[RegistrationSource] = mapped_column(
        pg_enum(RegistrationSource), default=RegistrationSource.CSV
    )
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_row: Mapped[dict] = mapped_column(JSON, default=dict)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    payment_status: Mapped[PaymentStatus] = mapped_column(
        pg_enum(PaymentStatus), default=PaymentStatus.PENDING, server_default=PaymentStatus.PENDING.value
    )
    payment_amount_inr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_screenshot_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    payment_screenshot_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    payment_screenshot_uploaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    team: Mapped["Team | None"] = relationship(back_populates="registration", uselist=False)
