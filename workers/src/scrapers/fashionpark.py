"""Fashion Park scraper — Shopify JSON API.

Fashion Park (fashionspark.com) runs on Shopify, which exposes public JSON
endpoints. No bot detection, no auth required.

Endpoints:
  GET /search/suggest.json?q={query}&resources[type]=product&resources[limit]=30
  GET /collections/{handle}/products.json?limit=250&page=1
  GET /collections/all/products.json?limit=250&page=N
"""

import json
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class FashionParkProduct:
    """Fashion Park product data."""
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


class FashionParkScraper:
    """Scraper for Fashion Park (fashionspark.com) using Shopify JSON API."""

    BASE_URL = "https://fashionspark.com"
    SEARCH_URL = "https://fashionspark.com/search/suggest.json?q={query}&resources[type]=product&resources[limit]=30"
    COLLECTION_URL = "https://fashionspark.com/collections/all/products.json?limit=250&page={page}"

    # Map product_type or tags to frontend categories
    CATEGORY_KEYWORDS = {
        "polera": "Poleras",
        "camiseta": "Poleras",
        "camisa": "Camisas",
        "blusa": "Camisas",
        "pantalon": "Pantalones",
        "pantalón": "Pantalones",
        "jean": "Pantalones",
        "bermuda": "Shorts",
        "short": "Shorts",
        "chaqueta": "Chaquetas",
        "abrigo": "Chaquetas",
        "parka": "Chaquetas",
        "blazer": "Chaquetas",
        "vestido": "Vestidos",
        "falda": "Faldas",
        "poleron": "Polerones",
        "polerón": "Polerones",
        "buzo": "Polerones",
        "sudadera": "Polerones",
    }

    def __init__(self):
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                timeout=20.0,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/131.0.0.0 Safari/537.36"
                    ),
                    "Accept": "application/json",
                    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
                },
            )
        return self._client

    def _infer_category(self, text: str) -> str:
        """Infer frontend category from product title, type, or tags."""
        t = text.lower()
        for keyword, category in self.CATEGORY_KEYWORDS.items():
            if keyword in t:
                return category
        return ""

    def _infer_gender(self, tags: list[str], title: str) -> str:
        """Infer gender from Shopify tags or product title."""
        tags_lower = [t.lower() for t in tags]
        title_lower = title.lower()
        if "hombre" in tags_lower or "hombre" in title_lower:
            return "hombre"
        elif "mujer" in tags_lower or "mujer" in title_lower:
            return "mujer"
        return ""

    async def search_products(self, query: str, max_items: int = 30) -> list[FashionParkProduct]:
        """Search products via Fashion Park Shopify suggest API."""
        client = await self._get_client()
        url = self.SEARCH_URL.format(query=query)
        products = []

        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            data = resp.json()
            results = data.get("resources", {}).get("results", {}).get("products", [])
            for item in results[:max_items]:
                product = self._parse_suggest_product(item, query)
                if product and product.name:
                    products.append(product)
        except Exception:
            pass

        return products[:max_items]

    async def scrape_category(self, category: str, max_items: int = 50) -> list[FashionParkProduct]:
        """Scrape products from a category using search."""
        return await self.search_products(category, max_items)

    def _parse_suggest_product(self, item: dict, query: str) -> Optional[FashionParkProduct]:
        """Parse a product from Shopify search suggest response."""
        if not isinstance(item, dict):
            return None

        title = item.get("title", "")
        if not title:
            return None

        # ID
        product_id = str(item.get("id", ""))

        # Price
        price = 0.0
        price_str = item.get("price", "0")
        try:
            price = float(str(price_str).replace(".", ""))
        except (ValueError, TypeError):
            pass

        # Image
        image_url = ""
        featured = item.get("featured_image")
        if isinstance(featured, dict):
            image_url = featured.get("url", "")
        elif isinstance(featured, str):
            image_url = featured

        # URL
        handle = item.get("handle", "")
        original_url = f"{self.BASE_URL}/products/{handle}" if handle else ""

        # Category from product type
        product_type = item.get("type", "")
        category = self._infer_category(product_type) or self._infer_category(title)

        # Gender from tags
        tags = item.get("tags", [])
        gender = self._infer_gender(tags, title)
        display_category = f"{category} {gender}".strip() if category else query

        # Availability
        availability = item.get("available", True)

        # Colors and sizes from tags (Shopify suggest doesn't return variants)
        colors = []
        sizes = []

        return FashionParkProduct(
            external_id=product_id,
            name=title,
            price=price,
            currency="CLP",
            image_url=image_url,
            category=display_category,
            sizes=sizes,
            colors=colors,
            description=f"Tipo: {product_type}" if product_type else "",
            availability=availability,
            original_url=original_url,
        )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
