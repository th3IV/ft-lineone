"""Paris scraper — Constructor.io API.

Paris.cl uses Constructor.io for search. We query the Constructor.io API
to get product listings without needing to scrape Paris.cl directly.

Workflow:
  1. Fetch Constructor.io key from JS bundle
  2. Search products via Constructor.io API
"""

import json
import re
from typing import Optional
from dataclasses import dataclass, field


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
    """Scraper for Paris (paris.cl) using Constructor.io API."""

    BASE_URL = "https://www.paris.cl"
    CNSTRC_BUNDLE_URL = "https://cnstrc.com/js/cust/cencosud_0BmS-e.js"
    CNSTRC_SEARCH_URL = "https://ac.cnstrc.com/search"

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

    def __init__(self):
        self._client = None
        self._cnstrc_key = None

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

    async def _get_cnstrc_key(self, client) -> Optional[str]:
        """Fetch Constructor.io key from Paris.cl JS bundle."""
        if self._cnstrc_key:
            return self._cnstrc_key

        try:
            print(json.dumps({"event": "paris_cnstrc_fetch", "url": self.CNSTRC_BUNDLE_URL}))
            resp = await client.get(self.CNSTRC_BUNDLE_URL)
            print(json.dumps({"event": "paris_cnstrc_response", "status": resp.status_code, "length": len(resp.text)}))
            if resp.status_code == 200:
                match = re.search(r'key[=:]\s*[\'"]?([a-zA-Z0-9_-]+)[\'"]?', resp.text)
                if match:
                    self._cnstrc_key = match.group(1)
                    print(json.dumps({"event": "paris_cnstrc_key_found", "key": self._cnstrc_key}))
                    return self._cnstrc_key
                else:
                    print(json.dumps({"event": "paris_cnstrc_key_not_found", "snippet": resp.text[:200]}))
        except Exception as e:
            print(json.dumps({"event": "paris_cnstrc_key_error", "error": str(e)}))

        return None

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
        client = await self._get_client()
        products = []

        try:
            # Get Constructor.io key
            key = await self._get_cnstrc_key(client)
            if not key:
                print(json.dumps({"event": "paris_search_error", "query": query, "error": "No Constructor.io key"}))
                return []

            # Search via Constructor.io
            print(json.dumps({"event": "paris_search_request", "query": query, "key": key, "max_items": max_items}))
            resp = await client.get(self.CNSTRC_SEARCH_URL, params={
                "key": key,
                "i": query,
                "num_results_per_page": max_items,
                "section": "Products",
            })

            print(json.dumps({"event": "paris_search_response", "query": query, "status": resp.status_code, "length": len(resp.text)}))
            if resp.status_code != 200:
                print(json.dumps({"event": "paris_search_error", "query": query, "status": resp.status_code, "body": resp.text[:500]}))
                return []

            data = resp.json()
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
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
