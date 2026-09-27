from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import DomainStatus, pg_enum
from app.models.mixins import TimestampMixin


class Domain(Base, TimestampMixin):
    __tablename__ = "domains"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DomainStatus] = mapped_column(
        pg_enum(DomainStatus), default=DomainStatus.ACTIVE, server_default=DomainStatus.ACTIVE.value
    )

    problem_statements: Mapped[list["ProblemStatement"]] = relationship(
        back_populates="domain",
        cascade="all, delete-orphan",
        order_by="ProblemStatement.order_index",
    )
    teams: Mapped[list["Team"]] = relationship(back_populates="domain")
    hints: Mapped[list["Hint"]] = relationship(back_populates="domain")
