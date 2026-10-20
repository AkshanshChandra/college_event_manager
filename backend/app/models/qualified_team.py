from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class QualifiedTeam(Base, TimestampMixin):
    """A team that qualified for Round 2, shown on the public Results page.

    Deliberately separate from Team/Registration — results are announced
    by name, not necessarily tied 1:1 to a portal account (and the list is
    entered by hand from the judges' decisions, not derived from submission
    data).
    """

    __tablename__ = "qualified_teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"))
    team_name: Mapped[str] = mapped_column(String(255))
    college: Mapped[str | None] = mapped_column(String(255), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=1)

    domain: Mapped["Domain"] = relationship(back_populates="qualified_teams")
