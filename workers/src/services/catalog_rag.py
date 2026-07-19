"""Catalog RAG (Retrieval-Augmented Generation) service.

Combines Vectorize semantic search with D1 hydration for intelligent product retrieval.
"""

import json
from typing import Optional

from services.database import DatabaseService
from services.vectorize import VectorizeService


class CatalogRAG:
    """RAG service for product catalog retrieval."""

    def __init__(self, env):
        self.env = env
        self.db = DatabaseService(env)
        self.vectorize = VectorizeService(env)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict = None,
    ) -> list[dict]:
        """
        Search catalog using semantic similarity.
        
        Args:
            query: Natural language search query
            top_k: Number of results to return
            filters: Optional metadata filters (store, gender, category, price_range)
        
        Returns:
            List of product dicts with similarity scores
        """
        # Build Vectorize filter
        filter_metadata = self._build_vectorize_filter(filters)
        
        # Semantic search in Vectorize
        matches = await self.vectorize.search(
            query=query,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )
        
        if not matches:
            return []
        
        # Hydrate from D1
        product_ids = [m["product_id"] for m in matches]
        products = await self._hydrate_products(product_ids)
        
        # Merge vector scores with product data
        results = []
        for match in matches:
            product = products.get(match["product_id"])
            if product:
                results.append({
                    **product,
                    "similarity_score": match["score"],
                })
        
        return results

    async def search_by_product(
        self,
        product_id: str,
        top_k: int = 5,
    ) -> list[dict]:
        """Find similar products to a given product."""
        product = await self.db.get_product(product_id)
        if not product:
            return []
        
        # Build query from product attributes
        query_parts = [
            product.name,
            product.category,
            " ".join(product.colors or []),
        ]
        query = " ".join(filter(None, query_parts))
        
        # Exclude the source product
        filters = {"product_id": {"$ne": product_id}}
        
        return await self.search(query, top_k=top_k + 1, filters=filters)

    def _build_vectorize_filter(self, filters: dict) -> dict:
        """Convert app filters to Vectorize metadata filter."""
        if not filters:
            return None
        
        vectorize_filter = {}
        
        if filters.get("store"):
            vectorize_filter["store"] = filters["store"]
        
        if filters.get("gender"):
            vectorize_filter["gender"] = filters["gender"]
        
        if filters.get("category"):
            vectorize_filter["category"] = {"$contains": filters["category"].lower()}
        
        if filters.get("min_price") is not None or filters.get("max_price") is not None:
            price_filter = {}
            if filters.get("min_price") is not None:
                price_filter["$gte"] = float(filters["min_price"])
            if filters.get("max_price") is not None:
                price_filter["$lte"] = float(filters["max_price"])
            vectorize_filter["price"] = price_filter
        
        return vectorize_filter if vectorize_filter else None

    async def _hydrate_products(self, product_ids: list[str]) -> dict:
        """Fetch full product data from D1 for given IDs."""
        if not product_ids:
            return {}
        
        # Use parameterized query for safety
        placeholders = ",".join(["?"] * len(product_ids))
        query = f"SELECT * FROM products WHERE id IN ({placeholders})"
        
        result = await self.db.db.prepare(query).bind(*product_ids).all()
        rows = result.get("results", []) if isinstance(result, dict) else result
        
        products = {}
        for row in rows:
            from services.database import ProductModel
            product = ProductModel(row)
            products[product.id] = {
                "id": product.id,
                "external_id": product.external_id,
                "name": product.name,
                "store": product.store,
                "price": product.price,
                "currency": product.currency,
                "category": product.category,
                "description": product.description,
                "original_url": product.original_url,
                "image_url": product.image_url,
                "image_urls": product.image_urls or [],
                "sizes": product.sizes or [],
                "colors": product.colors or [],
                "availability": product.availability,
            }
        
        return products

    # ============================================================
    # Index management (called on product UPSERT/DELETE)
    # ============================================================

    async def index_product(self, product) -> bool:
        """Index or update a product in Vectorize."""
        # Build searchable text from product attributes
        text_parts = [
            product.name,
            product.category,
            product.description or "",
            " ".join(product.colors or []),
            " ".join(product.sizes or []),
            product.store,
        ]
        text = " ".join(filter(None, text_parts))
        
        metadata = {
            "store": product.store,
            "category": product.category,
            "price": product.price,
            "gender": self._infer_gender(product),
            "product_id": product.id,
        }
        
        return await self.vectorize.upsert_product(product.id, text, metadata)

    async def delete_product(self, product_id: str) -> bool:
        """Remove a product from Vectorize index."""
        return await self.vectorize.delete_product(product_id)

    def _infer_gender(self, product) -> str:
        """Infer gender from product category/name."""
        cat = (product.category or "").lower()
        name = (product.name or "").lower()
        
        if any(k in cat for k in ["mujer", "women", "female", "damas", "ladies"]):
            return "mujer"
        if any(k in name for k in ["mujer", "dama", "lady"]):
            return "mujer"
        if any(k in cat for k in ["hombre", "men", "male", "caballero"]):
            return "hombre"
        if any(k in name for k in ["hombre", "caballero", "men"]):
            return "hombre"
        return "unisex"