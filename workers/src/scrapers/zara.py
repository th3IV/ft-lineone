"""Zara scraper using unofficial API endpoints (Async HTTP)."""

import httpx
from typing import Optional
from dataclasses import dataclass


@dataclass
class ZaraProduct:
    """Zara product data."""
    external_id: str
    name: str
    price: float
    currency: str
    image_url: str
    category: str
    sizes: list[str]
    colors: list[str]
    description: str
    availability: bool
    original_url: str


class ZaraScraper:
    """Scraper for Zara using unofficial API endpoints."""

    BASE_URL = "https://www.zara.com"
    API_BASE = "https://www.zara.com/itxrest"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Accept-Language": "es-CL,es;q=0.9",
            },
        )

    async def get_categories(self) -> list[dict]:
        """Get category tree from Zara API."""
        try:
            response = await self.client.get(
                f"{self.API_BASE}/2/catalog/category",
                params={"languageId": "-1"},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("categories", [])
        except Exception:
            return []

    async def get_category_products(
        self, category_id: int, page: int = 1, limit: int = 60
    ) -> list[dict]:
        """Get products from a specific category."""
        try:
            response = await self.client.get(
                f"{self.API_BASE}/2/catalog/category/{category_id}/products",
                params={
                    "page": page,
                    "pageSize": limit,
                    "languageId": "-1",
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("products", [])
        except Exception:
            return []

    async def get_product_details(self, product_id: int) -> Optional[dict]:
        """Get detailed product information."""
        try:
            response = await self.client.get(
                f"{self.API_BASE}/2/catalog/products/{product_id}",
                params={"languageId": "-1"},
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    async def search_products(self, query: str, limit: int = 30) -> list[dict]:
        """Search products by keyword."""
        try:
            response = await self.client.get(
                f"{self.API_BASE}/2/catalog/search",
                params={"query": query, "languageId": "-1"},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("products", [])[:limit]
        except Exception:
            return []

    def parse_product(self, raw_product: dict) -> ZaraProduct:
        """Parse raw product data into ZaraProduct."""
        name = raw_product.get("name", "")
        product_id = raw_product.get("id", "")
        seo_keyword = raw_product.get("seo", {}).get("keyword", "")
        seo_product_id = raw_product.get("seo", {}).get("productId", "")

        if seo_keyword and seo_product_id:
            original_url = f"{self.BASE_URL}/{seo_keyword}-p{seo_product_id}.html"
        else:
            original_url = f"{self.BASE_URL}/product/{product_id}"

        price_info = raw_product.get("price", {})
        price = price_info.get("price", 0)
        currency = price_info.get("currency", "CLP")

        image_url = ""
        images = raw_product.get("detail", {}).get("images", [])
        if images:
            image_url = images[0].get("url", "")

        sizes = []
        colors = []
        skus = raw_product.get("detail", {}).get("skus", [])
        for sku in skus:
            size = sku.get("name", "")
            color = sku.get("color", "")
            if size and size not in sizes:
                sizes.append(size)
            if color and color not in colors:
                colors.append(color)

        availability = any(
            sku.get("availability", "OUT_OF_STOCK") == "IN_STOCK"
            for sku in skus
        ) if skus else False

        return ZaraProduct(
            external_id=str(product_id),
            name=name,
            price=float(price) if price else 0.0,
            currency=currency,
            image_url=image_url,
            category="",
            sizes=sizes,
            colors=colors,
            description=raw_product.get("description", ""),
            availability=availability,
            original_url=original_url,
        )

    async def scrape_category(
        self, category_id: int, max_items: int = 50
    ) -> list[ZaraProduct]:
        """Scrape all products from a category."""
        products = []
        raw_products = await self.get_category_products(category_id, limit=max_items)

        for raw_product in raw_products[:max_items]:
            try:
                product = self.parse_product(raw_product)
                products.append(product)
            except Exception:
                continue

        return products

    async def scrape_search(
        self, query: str, max_items: int = 30
    ) -> list[ZaraProduct]:
        """Search and scrape products."""
        products = []
        raw_products = await self.search_products(query, limit=max_items)

        for raw_product in raw_products[:max_items]:
            try:
                product = self.parse_product(raw_product)
                products.append(product)
            except Exception:
                continue

        return products

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
