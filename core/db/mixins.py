from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

# BigInteger primary keys don't autoincrement on SQLite (only INTEGER does),
# so fall back to INTEGER there. On PostgreSQL BigInteger is used as-is, which
# lets the project run on either database.
PK_TYPE = BigInteger().with_variant(Integer, "sqlite")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class IDMixin:
    id: Mapped[int] = mapped_column(
        PK_TYPE,
        primary_key=True,
        index=True,
    )


class TableNameMixin:
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"


class ReprMixin:
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', None)})>"
