from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.models.product import Product
from app.infrastructure.persistence.postgres.models import Base, ProductModel


class ProductRepository:
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

    async def create(self, product: Product) -> Product:
        session = await self._get_session()
        model = ProductModel(
            id=product.id,
            external_id=product.external_id,
            store=product.store,
            name=product.name,
            description=product.description,
            price=product.price,
            currency=product.currency,
            image_url=product.image_url,
            category=product.category,
            sizes=product.sizes,
            colors=product.colors,
            scraped_at=product.scraped_at,
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        return self._to_domain(model)

    async def find_by_id(self, product_id: str) -> Product | None:
        session = await self._get_session()
        result = await session.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_all(self, page: int = 1, per_page: int = 20) -> tuple[list[Product], int]:
        session = await self._get_session()
        count_result = await session.execute(select(func.count(ProductModel.id)))
        total = count_result.scalar() or 0
        offset = (page - 1) * per_page
        result = await session.execute(
            select(ProductModel).offset(offset).limit(per_page)
        )
        models = result.scalars().all()
        return [self._to_domain(m) for m in models], total

    async def search(self, query: str, page: int = 1, per_page: int = 20) -> tuple[list[Product], int]:
        session = await self._get_session()
        search_filter = ProductModel.name.ilike(f"%{query}%")
        count_result = await session.execute(
            select(func.count(ProductModel.id)).where(search_filter)
        )
        total = count_result.scalar() or 0
        offset = (page - 1) * per_page
        result = await session.execute(
            select(ProductModel).where(search_filter).offset(offset).limit(per_page)
        )
        models = result.scalars().all()
        return [self._to_domain(m) for m in models], total

    async def find_by_store(self, store: str, page: int = 1, per_page: int = 20) -> tuple[list[Product], int]:
        session = await self._get_session()
        store_filter = ProductModel.store == store
        count_result = await session.execute(
            select(func.count(ProductModel.id)).where(store_filter)
        )
        total = count_result.scalar() or 0
        offset = (page - 1) * per_page
        result = await session.execute(
            select(ProductModel).where(store_filter).offset(offset).limit(per_page)
        )
        models = result.scalars().all()
        return [self._to_domain(m) for m in models], total

    async def update(self, product: Product) -> Product:
        session = await self._get_session()
        result = await session.execute(
            select(ProductModel).where(ProductModel.id == product.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError("Product not found")
        model.name = product.name
        model.description = product.description
        model.price = product.price
        model.currency = product.currency
        model.image_url = product.image_url
        model.category = product.category
        model.sizes = product.sizes
        model.colors = product.colors
        await session.commit()
        await session.refresh(model)
        return self._to_domain(model)

    async def delete(self, product_id: str) -> bool:
        session = await self._get_session()
        result = await session.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        await session.delete(model)
        await session.commit()
        return True

    def _to_domain(self, model: ProductModel) -> Product:
        return Product(
            id=str(model.id),
            external_id=model.external_id,
            store=model.store,
            name=model.name,
            description=model.description or "",
            price=model.price,
            currency=model.currency or "USD",
            image_url=model.image_url or "",
            category=model.category or "",
            sizes=model.sizes or [],
            colors=model.colors or [],
            scraped_at=model.scraped_at,
        )
