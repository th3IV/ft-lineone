from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.models.user import User
from app.infrastructure.persistence.postgres.models import UserModel


class UserRepository:
    def __init__(self, session: AsyncSession | None = None):
        self._session = session

    async def _get_session(self) -> AsyncSession:
        if self._session:
            return self._session
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        engine = create_async_engine(settings.DATABASE_URL.replace("psycopg2", "asyncpg"))
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        return session_maker()

    async def create(self, user: User) -> User:
        session = await self._get_session()
        model = UserModel(
            id=UUID(user.id),
            name=user.name,
            email=user.email,
            password_hash=user.password_hash,
            body_measurements=user.body_measurements,
            preferences=user.preferences,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        return self._to_domain(model)

    async def find_by_email(self, email: str) -> User | None:
        session = await self._get_session()
        result = await session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_id(self, user_id: str) -> User | None:
        session = await self._get_session()
        result = await session.execute(
            select(UserModel).where(UserModel.id == UUID(user_id))
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def update(self, user: User) -> User:
        session = await self._get_session()
        result = await session.execute(
            select(UserModel).where(UserModel.id == UUID(user.id))
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError("User not found")
        model.name = user.name
        model.email = user.email
        model.body_measurements = user.body_measurements
        model.preferences = user.preferences
        model.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=str(model.id),
            name=model.name,
            email=model.email,
            password_hash=model.password_hash,
            body_measurements=model.body_measurements or {},
            preferences=model.preferences or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
