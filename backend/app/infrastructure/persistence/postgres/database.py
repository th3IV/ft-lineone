from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.infrastructure.persistence.postgres.models import Base

_engine: AsyncEngine | None = None
_session_maker = None


def _get_url() -> str:
    url = settings.DATABASE_URL
    if "postgresql" in url:
        url = url.replace("psycopg2", "asyncpg")
    return url


async def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(_get_url())
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    return _engine


async def get_session_maker() -> async_sessionmaker[AsyncSession]:
    global _session_maker
    if _session_maker is None:
        engine = await get_engine()
        _session_maker = async_sessionmaker(engine, expire_on_commit=False)
    return _session_maker


async def get_session() -> AsyncSession:
    maker = await get_session_maker()
    return maker()


async def close_db():
    global _engine, _session_maker
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_maker = None
