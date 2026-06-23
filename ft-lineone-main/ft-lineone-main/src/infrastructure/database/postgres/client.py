from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from src.core.config import settings
from src.infrastructure.database.postgres.models import Base


class PostgresClient:
    _engine: AsyncEngine | None = None
    _session_factory: async_sessionmaker[AsyncSession] | None = None

    @classmethod
    def initialize(cls):
        if cls._engine is None:
            db_url = settings.SUPABASE_DB_URL
            if not db_url:
                raise ValueError("SUPABASE_DB_URL not configured")
            cls._engine = create_async_engine(db_url, echo=False, pool_pre_ping=True)
            cls._session_factory = async_sessionmaker(
                cls._engine, class_=AsyncSession, expire_on_commit=False
            )

    @classmethod
    async def create_tables(cls):
        cls.initialize()
        async with cls._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @classmethod
    async def close(cls):
        if cls._engine:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None

    @classmethod
    def get_session(cls) -> AsyncSession:
        if cls._session_factory is None:
            cls.initialize()
        return cls._session_factory()