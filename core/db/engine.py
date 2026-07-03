from sqlalchemy.ext.asyncio import AsyncEngine

from core.db.factory.engine import create_engine
from core.settings import core_settings

engine: AsyncEngine = create_engine(
    core_settings.DB_URL,
    echo=False,
)
