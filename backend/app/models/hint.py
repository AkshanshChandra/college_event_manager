from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import HintScope, PublishStatus, pg_enum
from app.models.mixins import TimestampMixin


class Hint(Base, TimestampMixin):
    __tablename__ = "hints"

    id: Mapped[int] = mapped_column(primary_key=True)
    week_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    scope: Mapped[HintScope] = mapped_column(pg_enum(HintScope), default=HintScope.GLOBAL)
    domain_id: Mapped[int | None] = mapped_column(
        ForeignKey("domains.id", ondelete="CASCADE"), nullable=True
    )
    publish_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[PublishStatus] = mapped_column(pg_enum(PublishStatus), default=PublishStatus.DRAFT)

    domain: Mapped["Domain | None"] = relationship(back_populates="hints")
