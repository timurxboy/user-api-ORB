from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from apps.users.models.user import User
from core.db.base import Base
from core.db.mixins import PK_TYPE


class VerificationCode(Base):
    """One-time email verification code issued at signup.

    A code confirms ownership of the email address. It is single-use (``used``)
    and time-limited (``expires_at``).
    """

    __tablename__ = "verification_codes"

    id: Mapped[int] = mapped_column(PK_TYPE, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    code: Mapped[str] = mapped_column(String(length=6), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Remove codes together with the owning user (see RefreshToken for rationale).
    user: Mapped[User] = relationship(
        backref=backref("verification_codes", cascade="all, delete-orphan"),
    )
