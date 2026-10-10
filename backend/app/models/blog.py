from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import PublishStatus, pg_enum
from app.models.mixins import TimestampMixin


class Blog(Base, TimestampMixin):
    """A one-time background-reading article for a domain — not recurring
    like the old weekly hints. Exactly one per domain, enforced by the
    unique constraint on domain_id.
    """

    __tablename__ = "blogs"

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[PublishStatus] = mapped_column(
        pg_enum(PublishStatus), default=PublishStatus.DRAFT, server_default=PublishStatus.DRAFT.value
    )

    domain: Mapped["Domain"] = relationship(back_populates="blog")
