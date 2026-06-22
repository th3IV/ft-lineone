from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.models.price_history import PriceHistory
from app.infrastructure.persistence.postgres.models import Base, PriceHistoryModel


class PriceHistoryRepository:
    def __init__(self, session: AsyncSession | None = None):
        self._session = session

    async def _get_session(self) -> AsyncSession:
        if self._session:
            return self._session
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        url = settings.DATABASE_URL
        if "postgresql" in url:
            url = url.replace("psycopg2", "asyncpg")
        engine = create_async_engine(url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        return session_maker()

    async def create(self, entry: PriceHistory) -> PriceHistory:
        session = await self._get_session()
        model = PriceHistoryModel(
            product_id=entry.product_id,
            external_id=entry.external_id,
            store=entry.store,
            price=entry.price,
            currency=entry.currency,
            scraped_at=entry.scraped_at,
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        return self._to_domain(model)

    async def find_by_product(self, product_id: str, limit: int = 20) -> list[PriceHistory]:
        session = await self._get_session()
        result = await session.execute(
            select(PriceHistoryModel)
            .where(PriceHistoryModel.product_id == product_id)
            .order_by(PriceHistoryModel.scraped_at.desc())
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_latest_by_product_and_store(self, product_id: str, store: str) -> PriceHistory | None:
        session = await self._get_session()
        result = await session.execute(
            select(PriceHistoryModel)
            .where(
                PriceHistoryModel.product_id == product_id,
                PriceHistoryModel.store == store,
            )
            .order_by(PriceHistoryModel.scraped_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    def _to_domain(self, model: PriceHistoryModel) -> PriceHistory:
        return PriceHistory(
            id=str(model.id),
            product_id=model.product_id,
            external_id=model.external_id or "",
            store=model.store,
            price=model.price,
            currency=model.currency or "USD",
            scraped_at=model.scraped_at,
        )
