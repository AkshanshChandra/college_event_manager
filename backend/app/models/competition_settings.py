from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class CompetitionSettings(Base, TimestampMixin):
    """Singleton-ish table: one row per named round (currently just "round_1")."""

    __tablename__ = "competition_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    round_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    round_label: Mapped[str] = mapped_column(String(128))
    submission_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    submission_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    allow_replacement: Mapped[bool] = mapped_column(Boolean, default=True)
    max_document_size_mb: Mapped[int] = mapped_column(Integer, default=25)
    max_video_size_mb: Mapped[int] = mapped_column(Integer, default=300)
    allowed_document_extensions: Mapped[str] = mapped_column(String(128), default="pdf,ppt,pptx")
    allowed_video_extensions: Mapped[str] = mapped_column(String(128), default="mp4,mov,webm")
