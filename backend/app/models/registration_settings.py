from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class RegistrationSettings(Base, TimestampMixin):
    """Singleton: one row controlling whether the public registration form
    accepts new submissions. Separate from CompetitionSettings since it isn't
    tied to a round's submission window.
    """

    __tablename__ = "registration_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
