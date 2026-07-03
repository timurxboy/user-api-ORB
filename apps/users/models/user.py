from sqlalchemy import Boolean, String, false, true
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from apps.users.domain.roles import Role
from core.db.base import Base
from core.db.mixins import IDMixin, ReprMixin, TableNameMixin, TimestampMixin
from core.security import check_password_hash, hash_password


class User(
    Base,
    IDMixin,
    TimestampMixin,
    TableNameMixin,
    ReprMixin,
):
    """Application user.

    A freshly registered user is unverified (``is_verified = False``) until
    they confirm their email via a verification code. Unverified users are
    automatically removed after a retention window (see the cleanup scheduler).
    """

    email: Mapped[str] = mapped_column(
        String(length=255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hashed: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )

    # Optional profile fields.
    first_name: Mapped[str | None] = mapped_column(
        String(length=100),
        nullable=True,
    )
    last_name: Mapped[str | None] = mapped_column(
        String(length=100),
        nullable=True,
    )

    role: Mapped[Role] = mapped_column(
        String(20),
        nullable=False,
        default=Role.USER,
    )

    # Dialect-aware defaults: false()/true() render as boolean literals on
    # PostgreSQL and as 0/1 on SQLite (a plain "false" string would be stored
    # verbatim by SQLite and read back as a truthy string). The Python-side
    # default keeps freshly created ORM instances consistent before reload.
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
        index=True,
    )

    # ---- password API ----

    @hybrid_property
    def password(self) -> str:
        raise AttributeError("Password is write-only")

    @password.setter
    def password(self, plaintext_password: str) -> None:
        self.password_hashed = hash_password(password=plaintext_password)

    def verify_password(self, password: str) -> bool:
        return check_password_hash(
            plain_password=password,
            hashed_password=self.password_hashed,
        )

    def __str__(self) -> str:
        return f"id={self.id} email={self.email}"
