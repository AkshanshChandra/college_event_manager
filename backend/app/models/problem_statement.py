from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import PublishStatus, pg_enum
from app.models.mixins import TimestampMixin


class ProblemStatement(Base, TimestampMixin):
    __tablename__ = "problem_statements"

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(
        ForeignKey("domains.id", ondelete="CASCADE"), unique=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints: Mapped[str | None] = mapped_column(Text, nullable=True)
    deliverables: Mapped[str | None] = mapped_column(Text, nullable=True)
    supporting_material_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[PublishStatus] = mapped_column(
        pg_enum(PublishStatus), default=PublishStatus.DRAFT, server_default=PublishStatus.DRAFT.value
    )

    domain: Mapped["Domain"] = relationship(back_populates="problem_statement")
