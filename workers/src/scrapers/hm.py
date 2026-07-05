"""H&M Chile scraper — VTEX Intelligent Search API.

H&M Chile (cl.hm.com) runs on VTEX + FastStore (Next.js).
VTEX exposes a public Intelligent Search API that returns structured JSON.

Endpoint:
  GET https://cl.hm.com/api/io/_v/api/intelligent-search/product_search/{query}?count=30
"""

import json
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class HMProduct:
    """H&M product data."""
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


class HMScraper:
    """Scraper for H&M Chile (cl.hm.com) using VTEX Intelligent Search API."""

    BASE_URL = "https://cl.hm.com"
    SEARCH_URL = "https://cl.hm.com/api/io/_v/api/intelligent-search/product_search/{query}?count=30"

    # Map VTEX product categories / keywords to frontend categories
    CATEGORY_KEYWORDS = {
        "polera": "Poleras",
        "camiseta": "Poleras",
        "remera": "Poleras",
        "t-shirt": "Poleras",
        "camisa": "Camisas",
        "blusa": "Camisas",
        "shirt": "Camisas",
        "pantalon": "Pantalones",
        "pantalón": "Pantalones",
        "jean": "Pantalones",
        "jeans": "Pantalones",
        "bermuda": "Shorts",
        "short": "Shorts",
        "chaqueta": "Chaquetas",
        "abrigo": "Chaquetas",
        "parka": "Chaquetas",
        "blazer": "Chaquetas",
        "vestido": "Vestidos",
        "dress": "Vestidos",
        "falda": "Faldas",
        "skirt": "Faldas",
        "poleron": "Polerones",
        "polerón": "Polerones",
        "buzo": "Polerones",
        "sudadera": "Polerones",
        "sweatshirt": "Polerones",
        "hoodie": "Polerones",
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
        """Infer frontend category from product name or category tree."""
        t = text.lower()
        for keyword, category in self.CATEGORY_KEYWORDS.items():
            if keyword in t:
                return category
        return ""

    async def search_products(self, query: str, max_items: int = 30) -> list[HMProduct]:
        """Search products via H&M VTEX Intelligent Search API."""
        client = await self._get_client()
        url = self.SEARCH_URL.format(query=query)
        products = []

        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            data = resp.json()
            items = data.get("products", [])
            for item in items[:max_items]:
                product = self._parse_product(item, query)
                if product and product.name:
                    products.append(product)
        except Exception:
            pass

        return products[:max_items]

    async def scrape_category(self, category: str, max_items: int = 50) -> list[HMProduct]:
        """Scrape products from a category using search."""
        return await self.search_products(category, max_items)

    def _parse_product(self, item: dict, query: str) -> Optional[HMProduct]:
        """Parse a product from VTEX search response."""
        if not isinstance(item, dict):
            return None

        # Product ID (VTEX uses productId or item.productId)
        product_id = str(item.get("productId", "") or item.get("id", ""))
        if not product_id:
            return None

        # Name
        name = item.get("productName", "") or item.get("name", "")
        if not name:
            return None

        # Price (VTEX items[0].sellingPrice or items[0].price)
        price = 0.0
        items_list = item.get("items", [])
        if items_list and isinstance(items_list, list):
            first_item = items_list[0]
            selling_price = first_item.get("sellingPrice", 0) or first_item.get("price", 0)
            try:
                price = float(selling_price) / 100  # VTEX prices in cents
            except (ValueError, TypeError):
                pass

        # Image
        image_url = ""
        items_list = item.get("items", [])
        if items_list and isinstance(items_list, list):
            first_item = items_list[0]
            images = first_item.get("images", [])
            if images and isinstance(images, list):
                image_url = images[0].get("imageUrl", "")

        # URL
        link = item.get("link", "") or item.get("linkText", "")
        original_url = f"{self.BASE_URL}{link}" if link and not link.startswith("http") else link

        # Category from categoryTree
        category_tree = item.get("categories", [])
        category = ""
        if category_tree and isinstance(category_tree, list):
            # Use last category in tree (most specific)
            for cat in category_tree:
                cat_name = cat.get("name", "") if isinstance(cat, dict) else str(cat)
                mapped = self._infer_category(cat_name)
                if mapped:
                    category = mapped
                    break

        if not category:
            category = self._infer_category(name) or self._infer_category(query)

        # Gender from category tree or query
        gender = ""
        q = query.lower()
        if "hombre" in q or "man" in q:
            gender = "hombre"
        elif "mujer" in q or "woman" in q:
            gender = "mujer"

        display_category = f"{category} {gender}".strip() if category else query

        # Sizes from items[0].sellers[0].commertialOffer.Availabilities
        sizes = []
        colors = []
        if items_list and isinstance(items_list, list):
            for item_obj in items_list:
                if not isinstance(item_obj, dict):
                    continue
                # Size from item name or specifications
                size_name = item_obj.get("nameComplete", "") or item_obj.get("name", "")
                sellers = item_obj.get("sellers", [])
                if sellers and isinstance(sellers, list):
                    offer = sellers[0].get("commertialOffer", {})
                    avail = offer.get("AvailableQuantity", 0)
                    if avail > 0 and size_name:
                        # Extract size from name (e.g., "POLERA ALGODON REGULAR - M")
                        parts = size_name.split(" - ")
                        if len(parts) > 1:
                            sizes.append(parts[-1].strip())

        # Availability
        availability = True
        if items_list and isinstance(items_list, list):
            first_item = items_list[0]
            sellers = first_item.get("sellers", [])
            if sellers and isinstance(sellers, list):
                offer = sellers[0].get("commertialOffer", {})
                if offer.get("AvailableQuantity", 0) == 0:
                    availability = False

        return HMProduct(
            external_id=product_id,
            name=name,
            price=price,
            currency="CLP",
            image_url=image_url,
            category=display_category,
            sizes=sizes,
            colors=colors,
            description="",
            availability=availability,
            original_url=original_url,
        )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
