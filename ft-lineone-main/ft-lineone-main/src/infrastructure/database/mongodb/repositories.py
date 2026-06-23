from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from src.infrastructure.database.mongodb.models import ProductDocument as Product
from src.core.config import settings


class MongoProductRepository:
    def __init__(self, client: AsyncIOMotorClient | None = None):
        self._client = client or AsyncIOMotorClient(settings.MONGODB_URI)
        self._db = self._client.get_default_database()
        self._initialized = False

    async def initialize(self):
        if not self._initialized:
            await init_beanie(database=self._db, document_models=[Product])
            self._initialized = True

    async def save(self, product: Product) -> Product:
        await self.initialize()
        existing = await Product.find_one(
            Product.external_id == product.external_id,
            Product.store == product.store,
        )
        if existing:
            product.id = existing.id
            await product.replace()
        else:
            await product.insert()
        return product

    async def bulk_upsert(self, products: List[Product]) -> int:
        await self.initialize()
        saved = 0
        for product in products:
            await self.save(product)
            saved += 1
        return saved

    async def find_by_external_id(self, external_id: str, store: str) -> Optional[Product]:
        await self.initialize()
        return await Product.find_one(Product.external_id == external_id, Product.store == store)

    async def find_all(self, page: int = 1, per_page: int = 20) -> tuple[List[Product], int]:
        await self.initialize()
        total = await Product.count()
        products = await Product.find().skip((page - 1) * per_page).limit(per_page).to_list()
        return products, total

    async def find_by_category(self, category: str, page: int = 1, per_page: int = 20) -> List[Product]:
        await self.initialize()
        return await Product.find(Product.category == category).skip((page - 1) * per_page).limit(per_page).to_list()

    async def find_by_store(self, store: str, page: int = 1, per_page: int = 20) -> List[Product]:
        await self.initialize()
        return await Product.find(Product.store == store).skip((page - 1) * per_page).limit(per_page).to_list()

    async def search(self, query: str, page: int = 1, per_page: int = 20) -> List[Product]:
        await self.initialize()
        regex = {"$regex": query, "$options": "i"}
        return await Product.find({"$or": [{"name": regex}, {"description": regex}]}) \
            .skip((page - 1) * per_page).limit(per_page).to_list()