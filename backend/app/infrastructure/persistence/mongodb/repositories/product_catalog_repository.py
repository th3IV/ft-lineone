from typing import Any
from app.infrastructure.persistence.mongodb.database import mongodb_client

class ProductCatalogRepository:
    def __init__(self):
        self._db = mongodb_client.get_database()
        self._collection = self._db.product_catalogs

    async def insert_raw_product(self, product_data: dict):
        """Inserts unstructured scraping data into MongoDB."""
        result = await self._collection.insert_one(product_data)
        return result.inserted_id

    async def find_by_store(self, store: str):
        """Retrieves raw products for a specific store."""
        cursor = self._collection.find({"store": store})
        return await cursor.to_list(length=100)

    async def find_by_category(self, category: str):
        """Retrieves raw products for a specific category."""
        cursor = self._collection.find({"category": category})
        return await cursor.to_list(length=100)

    async def update_product(self, product_id: str, update_data: dict):
        """Updates a raw product entry."""
        await self._collection.update_one({"_id": product_id}, {"$set": update_data})
