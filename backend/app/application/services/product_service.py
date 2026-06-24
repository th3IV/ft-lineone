from app.domain.models.product import Product
from app.infrastructure.persistence.postgres.repositories.product_repository import (
    ProductRepository,
)


class ProductService:
    def __init__(self, product_repo: ProductRepository | None = None):
        self._product_repo = product_repo or ProductRepository()

    async def get_catalog(self, page: int = 1, per_page: int = 20) -> tuple[list[Product], int]:
        return await self._product_repo.find_all(page=page, per_page=per_page)

    async def get_by_id(self, product_id: str) -> Product | None:
        return await self._product_repo.find_by_id(product_id)

    async def search(self, query: str, page: int = 1, per_page: int = 20) -> tuple[list[Product], int]:
        return await self._product_repo.search(query=query, page=page, per_page=per_page)

    async def get_by_store(self, store: str, page: int = 1, per_page: int = 20) -> tuple[list[Product], int]:
        return await self._product_repo.find_by_store(store=store, page=page, per_page=per_page)

    async def upsert_product(self, product: Product) -> Product:
        return await self._product_repo.upsert(product)
