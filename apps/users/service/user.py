from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.users.domain.roles import Role
from apps.users.models.user import User
from apps.users.schemas.user import UserUpdate
from core.datetime import utcnow
from core.settings import core_settings


class UserService:
    """User management: listing, retrieval, partial update and deletion."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def list_query(self):
        """Return a base SELECT for paginated user listing."""
        return select(User).order_by(User.id)

    async def get(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def update(
        self,
        user: User,
        data: UserUpdate,
        *,
        allow_privileged: bool,
    ) -> User:
        """Apply a partial update.

        ``role`` and ``is_active`` are privileged fields and are ignored unless
        ``allow_privileged`` is set (admin callers).
        """
        payload = data.model_dump(exclude_unset=True)

        if not allow_privileged:
            payload.pop("role", None)
            payload.pop("is_active", None)

        if "email" in payload and payload["email"] != user.email:
            existing = await self.session.execute(
                select(User).where(User.email == payload["email"])
            )
            if existing.scalar_one_or_none():
                raise ValueError("Email already registered")

        for field, value in payload.items():
            setattr(user, field, value)

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def cleanup_unverified(self) -> int:
        """Delete users that stayed unverified past the retention window.

        Unverified accounts are removed after ``UNVERIFIED_RETENTION_DAYS``
        (default 2 days).
        """
        cutoff = utcnow() - timedelta(days=core_settings.UNVERIFIED_RETENTION_DAYS)
        result = await self.session.execute(
            delete(User).where(
                User.is_verified.is_(False),
                User.role != Role.ADMIN,
                User.created_at < cutoff,
            )
        )
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return result.rowcount
