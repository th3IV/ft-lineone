"""Paris scraper — Constructor.io API using js.fetch.

Paris.cl uses Constructor.io for search. We query the Constructor.io API
directly using js.fetch (Cloudflare Workers Python compatible).

The API key is extracted from the Constructor.io bundle URL:
  URL: https://cnstrc.com/js/cust/cencosud_0BmS-e.js
  Key: cencosud_0BmS-e
"""

import json
import re
from typing import Optional
from dataclasses import dataclass, field
from urllib.parse import urlencode

import js
from pyodide.ffi import to_js as _to_js
from js import Object


def to_js(obj):
    """Convert Python objects to JS with dict_converter."""
    return _to_js(obj, dict_converter=Object.fromEntries)


@dataclass
class ParisProduct:
    """Paris product data."""
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
    image_urls: list[str] = field(default_factory=list)


class ParisScraper:
    """Scraper for Paris (paris.cl) using Constructor.io API with js.fetch."""

    BASE_URL = "https://www.paris.cl"
    CNSTRC_SEARCH_URL = "https://ac.cnstrc.com/search"
    # Key extracted from: https://cnstrc.com/js/cust/cencosud_0BmS-e.js
    CNSTRC_KEY = "cencosud_0BmS-e"

    # Category keywords for mapping search queries -> frontend categories
    CATEGORY_KEYWORDS = {
        "polera": "Poleras",
        "camiseta": "Poleras",
        "camisa": "Camisas",
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

    def _infer_category(self, query: str) -> str:
        """Infer frontend category from search query keywords."""
        q = query.lower()
        for keyword, category in self.CATEGORY_KEYWORDS.items():
            if keyword in q:
                return category
        return ""

    def _infer_gender(self, query: str) -> str:
        """Infer gender from search query."""
        q = query.lower()
        if "hombre" in q:
            return "hombre"
        elif "mujer" in q:
            return "mujer"
        return ""

    async def search_products(self, query: str, max_items: int = 30) -> list[ParisProduct]:
        """Search products via Constructor.io API."""
        products = []

        try:
            # Search via Constructor.io
            params = urlencode({
                "key": self.CNSTRC_KEY,
                "i": query,
                "num_results_per_page": str(max_items),
                "section": "Products",
            })
            url = f"{self.CNSTRC_SEARCH_URL}?{params}"

            print(json.dumps({"event": "paris_search_request", "query": query, "url": url}))

            resp = await js.fetch(url, to_js({
                "method": "GET",
                "headers": {"Accept": "application/json"},
            }))

            print(json.dumps({"event": "paris_search_response", "ok": resp.ok, "status": resp.status}))

            if not resp.ok:
                error_text = await resp.text()
                print(json.dumps({"event": "paris_search_error", "query": query, "status": resp.status, "error": error_text[:500]}))
                return []

            data = json.loads(await resp.text())
            results = data.get("response", {}).get("results", [])
            print(json.dumps({"event": "paris_search_results", "query": query, "results_count": len(results)}))

            category = self._infer_category(query)
            gender = self._infer_gender(query)
            display_category = f"{category} {gender}".strip() if category else query

            seen_ids = set()

            for item in results:
                if len(products) >= max_items:
                    break

                item_data = item.get("data", {})
                if not item_data:
                    continue

                # Extract fields from Constructor.io response
                external_id = str(item_data.get("id", "") or item.get("id", ""))
                name = item_data.get("product_name", "") or item_data.get("name", "")
                if not name:
                    continue

                # Deduplicate
                if external_id in seen_ids:
                    continue
                seen_ids.add(external_id)

                # Price
                price = 0.0
                price_val = item_data.get("price", 0) or item_data.get("minimum_price", 0)
                try:
                    price = float(price_val)
                except (ValueError, TypeError):
                    pass

                # URL
                url = item_data.get("url", "")
                if url and not url.startswith("http"):
                    url = f"{self.BASE_URL}{url}"

                # Image
                image_url = item_data.get("image_url", "") or item_data.get("image", "")
                image_urls = []
                if image_url:
                    image_urls.append(image_url)

                # Availability
                availability = True
                if item_data.get("availability") == "OutOfStock":
                    availability = False

                products.append(ParisProduct(
                    external_id=external_id,
                    name=name,
                    price=price,
                    currency="CLP",
                    image_url=image_urls[0] if image_urls else "",
                    category=display_category,
                    sizes=[],
                    colors=[],
                    description="",
                    availability=availability,
                    original_url=url,
                    image_urls=image_urls,
                ))

            print(json.dumps({"event": "paris_search_success", "query": query, "products_found": len(products)}))

        except Exception as e:
            print(json.dumps({"event": "paris_search_error", "query": query, "error": str(e)}))

        return products[:max_items]

    async def scrape_category(self, category: str, max_items: int = 50) -> list[ParisProduct]:
        """Scrape products from a category using search."""
        return await self.search_products(category, max_items)

    async def close(self):
        """No-op for js.fetch (no client to close)."""
        pass
