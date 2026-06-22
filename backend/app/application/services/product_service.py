from app.domain.models.product import Product
from app.domain.models.price_history import PriceHistory
from app.infrastructure.persistence.postgres.repositories.product_repository import (
    ProductRepository,
)
from app.infrastructure.persistence.postgres.repositories.price_history_repository import (
    PriceHistoryRepository,
)


class ProductService:
    def __init__(
        self,
        product_repo: ProductRepository | None = None,
        price_history_repo: PriceHistoryRepository | None = None,
    ):
        self._product_repo = product_repo or ProductRepository()
        self._price_history_repo = price_history_repo or PriceHistoryRepository()

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

    async def record_price(self, product: Product) -> PriceHistory:
        entry = PriceHistory(
            product_id=product.id or "",
            external_id=product.external_id,
            store=product.store,
            price=product.price,
            currency=product.currency,
        )
        return await self._price_history_repo.create(entry)

    async def get_price_comparison(self, product_id: str) -> dict:
        product = await self._product_repo.find_by_id(product_id)
        if not product:
            return {"product_id": product_id, "matches": []}

        matches = await self._product_repo.find_by_normalized_name(
            product.normalized_name, exclude_store=product.store
        )
        all_products = [product] + matches
        all_products.sort(key=lambda p: p.price)

        result = []
        for p in all_products:
            hist = await self._price_history_repo.get_latest_by_product_and_store(
                p.id or "", p.store
            )
            result.append({
                "id": p.id,
                "store": p.store,
                "name": p.name,
                "price": p.price,
                "currency": p.currency,
                "image_url": p.image_url,
                "product_url": p.image_url,
                "last_checked": hist.scraped_at.isoformat() if hist else None,
            })
        return {
            "product_id": product_id,
            "product_name": product.name,
            "cheapest": result[0] if result else None,
            "matches": result,
        }
