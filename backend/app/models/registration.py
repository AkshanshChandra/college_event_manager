from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import RegistrationSource, pg_enum
from app.models.mixins import TimestampMixin


class Registration(Base, TimestampMixin):
    """Raw record synced from the Google Form response sheet (or CSV import).

    This is the source of truth for "did this email actually register".
    A Team/User is only ever created from a row that exists here.
    """

    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_name: Mapped[str] = mapped_column(String(255))
    leader_name: Mapped[str] = mapped_column(String(255))
    leader_email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    leader_phone: Mapped[str] = mapped_column(String(32))
    college: Mapped[str] = mapped_column(String(255))
    domain_slug: Mapped[str] = mapped_column(String(64))
    members_raw: Mapped[list] = mapped_column(JSON, default=list)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[RegistrationSource] = mapped_column(
        pg_enum(RegistrationSource), default=RegistrationSource.CSV
    )
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_row: Mapped[dict] = mapped_column(JSON, default=dict)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    team: Mapped["Team | None"] = relationship(back_populates="registration", uselist=False)
