from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.infrastructure.persistence.postgres.models import Base

_engine = None
_session_maker = None


async def get_engine():
    global _engine
    if _engine is None:
        url = settings.DATABASE_URL
        if "postgresql" in url:
            url = url.replace("psycopg2", "asyncpg")
        _engine = create_async_engine(url, echo=False)
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    return _engine


async def get_session() -> AsyncSession:
    global _session_maker
    if _session_maker is None:
        engine = await get_engine()
        _session_maker = async_sessionmaker(engine, expire_on_commit=False)
    return _session_maker()
