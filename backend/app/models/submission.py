from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SubmissionFileType, SubmissionStatus, pg_enum
from app.models.mixins import TimestampMixin


class Submission(Base, TimestampMixin):
    """One versioned snapshot of a team's Round 1 submission.

    A team may accumulate several versions before the deadline; exactly one
    is flagged is_active_version and represents "the" submission for admin views.
    """

    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[SubmissionStatus] = mapped_column(
        pg_enum(SubmissionStatus), default=SubmissionStatus.SUBMITTED
    )
    is_active_version: Mapped[bool] = mapped_column(Boolean, default=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    team: Mapped["Team"] = relationship(back_populates="submissions")
    files: Mapped[list["SubmissionFile"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )


class SubmissionFile(Base, TimestampMixin):
    __tablename__ = "submission_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE")
    )
    file_type: Mapped[SubmissionFileType] = mapped_column(pg_enum(SubmissionFileType))
    original_filename: Mapped[str] = mapped_column(String(512))
    storage_key: Mapped[str] = mapped_column(String(1024))
    content_type: Mapped[str] = mapped_column(String(128))
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    submission: Mapped["Submission"] = relationship(back_populates="files")
