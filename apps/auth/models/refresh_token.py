from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from apps.users.models.user import User
from core.db.base import Base
from core.db.mixins import PK_TYPE


class RefreshToken(Base):
    """Persisted refresh token used to mint new access tokens."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(PK_TYPE, primary_key=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Delete tokens together with the owning user (ORM-level cascade works on
    # both SQLite and PostgreSQL; the DB-level ON DELETE CASCADE above is a
    # safety net for direct SQL deletes).
    user: Mapped[User] = relationship(
        backref=backref("refresh_tokens", cascade="all, delete-orphan"),
    )
