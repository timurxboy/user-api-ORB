from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository[T]:
    """
    Generic async repository.
    DOES NOT commit or rollback.
    """

    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def get_by_id(self, entity_id: int) -> T | None:
        result = await self.session.execute(select(self.model).where(self.model.id == entity_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[T]:
        result = await self.session.execute(select(self.model).limit(limit).offset(offset))
        return result.scalars().all()

    async def add(self, entity: T) -> T:
        self.session.add(entity)
        return entity

    async def delete_by_id(self, entity_id: int) -> bool:
        result = await self.session.execute(delete(self.model).where(self.model.id == entity_id))
        return result.rowcount > 0
