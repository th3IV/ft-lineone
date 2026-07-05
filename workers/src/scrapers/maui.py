"""Maui scraper — Magento 2 GraphQL API.

Maui & Sons Chile (mauiandsons.cl) runs on Magento 2 with a public
GraphQL endpoint at POST /graphql. No bot detection on GraphQL.

Queries:
  products(search: "polera", pageSize: 30) { items { name, sku, url_key, price_range, image } }
  categoryList(filters: { url_path: { eq: "hombre/vestuario/poleras" } }) { products { ... } }
"""

import json
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class MauiProduct:
    """Maui product data."""
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


# Map Maui category url_paths to frontend categories
CATEGORY_PATH_MAP = {
    "hombre/vestuario/poleras": "Poleras",
    "mujer/vestuario/poleras": "Poleras",
    "hombre/vestuario/camisas": "Camisas",
    "mujer/vestuario/camisas": "Camisas",
    "hombre/vestuario/pantalones": "Pantalones",
    "mujer/vestuario/pantalones": "Pantalones",
    "hombre/vestuario/jeans": "Pantalones",
    "mujer/vestuario/jeans": "Pantalones",
    "hombre/vestuario/shorts": "Shorts",
    "mujer/vestuario/shorts": "Shorts",
    "hombre/vestuario/parkas-y-chaquetas": "Chaquetas",
    "mujer/vestuario/parkas-y-chaquetas": "Chaquetas",
    "mujer/vestuario/vestidos": "Vestidos",
    "mujer/vestuario/faldas": "Faldas",
    "hombre/vestuario/polerones": "Polerones",
    "mujer/vestuario/polerones": "Polerones",
}

# Map keywords to frontend categories (for search queries)
CATEGORY_KEYWORDS = {
    "polera": "Poleras",
    "camiseta": "Poleras",
    "camisa": "Camisas",
    "blusa": "Camisas",
    "pantalon": "Pantalones",
    "jean": "Pantalones",
    "short": "Shorts",
    "bermuda": "Shorts",
    "chaqueta": "Chaquetas",
    "parka": "Chaquetas",
    "abrigo": "Chaquetas",
    "vestido": "Vestidos",
    "falda": "Faldas",
    "poleron": "Polerones",
    "buzo": "Polerones",
    "sudadera": "Polerones",
}


class MauiScraper:
    """Scraper for Maui & Sons (mauiandsons.cl) using Magento 2 GraphQL."""

    BASE_URL = "https://mauiandsons.cl"
    GRAPHQL_URL = "https://mauiandsons.cl/graphql"

    # Search query - fetches products with all needed fields
    SEARCH_QUERY = """
    query SearchProducts($search: String!, $pageSize: Int!) {
        products(search: $search, pageSize: $pageSize) {
            total_count
            items {
                name
                sku
                url_key
                stock_status
                price_range {
                    minimum_price {
                        regular_price { value currency }
                        final_price { value currency }
                        discount { amount_off percent_off }
                    }
                }
                image { url label }
                description { html }
                ... on ConfigurableProduct {
                    configurable_options {
                        label
                        values { label }
                    }
                    variants {
                        product { name sku price_range { minimum_price { regular_price { value } } } }
                        attributes { code label value_index }
                    }
                }
            }
        }
    }
    """

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
                    "Content-Type": "application/json",
                    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
                },
            )
        return self._client

    def _infer_category(self, text: str) -> str:
        """Infer frontend category from text."""
        t = text.lower()
        for keyword, category in CATEGORY_KEYWORDS.items():
            if keyword in t:
                return category
        return ""

    async def _graphql_query(self, query: str, variables: dict = None) -> Optional[dict]:
        """Execute a GraphQL query."""
        client = await self._get_client()
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            resp = await client.post(self.GRAPHQL_URL, json=payload)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    async def search_products(self, query: str, max_items: int = 30) -> list[MauiProduct]:
        """Search products via Magento 2 GraphQL."""
        data = await self._graphql_query(
            self.SEARCH_QUERY,
            {"search": query, "pageSize": max_items}
        )

        if not data:
            return []

        products_data = data.get("data", {}).get("products", {})
        items = products_data.get("items", [])

        # Infer category from query
        category = self._infer_category(query)
        gender = ""
        q = query.lower()
        if "hombre" in q:
            gender = "hombre"
        elif "mujer" in q:
            gender = "mujer"
        display_category = f"{category} {gender}".strip() if category else query

        products = []
        for item in items[:max_items]:
            product = self._parse_product(item, display_category)
            if product and product.name:
                products.append(product)

        return products[:max_items]

    async def scrape_category(self, category: str, max_items: int = 50) -> list[MauiProduct]:
        """Scrape products from a category.

        category: internal slug like "hombre-poleras" or "mujer-chaquetas"
        """
        # Convert slug to url_path (e.g., "hombre-poleras" -> "hombre/vestuario/poleras")
        url_path = category.replace("-", "/")
        if "/vestuario/" not in url_path:
            # Try to insert vestuario
            parts = url_path.split("-")
            if len(parts) == 2:
                url_path = f"{parts[0]}/vestuario/{parts[1]}"

        # Use search with category filter
        search_term = url_path.split("/")[-1]  # Get the clothing type
        return await self.search_products(search_term, max_items)

    def _parse_product(self, item: dict, category: str) -> Optional[MauiProduct]:
        """Parse a product from GraphQL response."""
        if not isinstance(item, dict):
            return None

        name = item.get("name", "")
        if not name:
            return None

        sku = item.get("sku", "")
        url_key = item.get("url_key", "")

        # Price
        price = 0.0
        price_range = item.get("price_range", {})
        min_price = price_range.get("minimum_price", {})
        final_price = min_price.get("final_price", {})
        price_val = final_price.get("value", 0)
        try:
            price = float(price_val)
        except (ValueError, TypeError):
            pass

        # Image
        image_url = ""
        image_data = item.get("image", {})
        if isinstance(image_data, dict):
            image_url = image_data.get("url", "")

        # URL
        original_url = f"{self.BASE_URL}/{url_key}.html" if url_key else ""

        # Sizes from configurable options
        sizes = []
        colors = []
        configurable = item.get("configurable_options", [])
        if isinstance(configurable, list):
            for opt in configurable:
                if isinstance(opt, dict):
                    label = opt.get("label", "").lower()
                    values = opt.get("values", [])
                    if "talla" in label or "size" in label:
                        for v in values:
                            if isinstance(v, dict):
                                sizes.append(v.get("label", ""))
                    elif "color" in label:
                        for v in values:
                            if isinstance(v, dict):
                                colors.append(v.get("label", ""))

        # Availability
        availability = item.get("stock_status", "") == "IN_STOCK"

        # Description (strip HTML)
        desc_html = ""
        desc_data = item.get("description", {})
        if isinstance(desc_data, dict):
            desc_html = desc_data.get("html", "")
        # Simple HTML tag removal
        import re
        description = re.sub(r"<[^>]+>", "", desc_html).strip()[:200]

        return MauiProduct(
            external_id=sku,
            name=name,
            price=price,
            currency="CLP",
            image_url=image_url,
            category=category,
            sizes=sizes,
            colors=colors,
            description=description,
            availability=availability,
            original_url=original_url,
        )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
