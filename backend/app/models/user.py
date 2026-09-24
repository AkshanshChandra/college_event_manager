from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AccountStatus, UserRole, pg_enum
from app.models.mixins import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(pg_enum(UserRole), default=UserRole.PARTICIPANT)
    status: Mapped[AccountStatus] = mapped_column(
        pg_enum(AccountStatus), default=AccountStatus.PENDING_ACTIVATION
    )
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, unique=True
    )

    team: Mapped["Team | None"] = relationship(back_populates="leader")
    activation_tokens: Mapped[list["ActivationToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
