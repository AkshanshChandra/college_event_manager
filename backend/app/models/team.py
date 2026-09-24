from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class Team(Base, TimestampMixin):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    college: Mapped[str] = mapped_column(String(255))
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"))
    registration_id: Mapped[int] = mapped_column(
        ForeignKey("registrations.id", ondelete="RESTRICT"), unique=True
    )

    domain: Mapped["Domain"] = relationship(back_populates="teams")
    registration: Mapped["Registration"] = relationship(back_populates="team")
    members: Mapped[list["TeamMember"]] = relationship(
        back_populates="team", cascade="all, delete-orphan"
    )
    leader: Mapped["User | None"] = relationship(back_populates="team", uselist=False)
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="team", cascade="all, delete-orphan", order_by="Submission.version"
    )


class TeamMember(Base, TimestampMixin):
    __tablename__ = "team_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)

    team: Mapped["Team"] = relationship(back_populates="members")
