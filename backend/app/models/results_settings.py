from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class ResultsSettings(Base, TimestampMixin):
    """Singleton: whether the public Results page is live, plus an optional
    short announcement blurb shown at the top of it.
    """

    __tablename__ = "results_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    announcement: Mapped[str | None] = mapped_column(String(500), nullable=True)
