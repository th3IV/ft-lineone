"""Falabella scraper — HTTP direct with Next.js SSR JSON extraction.

Falabella renders products via React/Next.js with server-side rendering.
Product data is embedded in the HTML inside a <script id="__NEXT_DATA__"> tag
as JSON with the structure {"props":{"pageProps":{"results":[...]}}}.

This scraper fetches the HTML and parses the JSON directly — no Playwright needed.
"""

import json
import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class FalabellaProduct:
    """Falabella product data."""
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


# Falabella GSCCategoryId → frontend category
CATEGORY_MAP = {
    "G08020703": "Poleras",
    "G08020701": "Camisas",
    "G08020704": "Pantalones",
    "G08020705": "Shorts",
    "G08020706": "Chaquetas",
    "G08020702": "Vestidos",
    "G08020707": "Faldas",
    "G08020708": "Polerones",
}


class FalabellaScraper:
    """Scraper for Falabella (falabella.com) using HTTP direct + SSR JSON."""

    BASE_URL = "https://www.falabella.com"
    SEARCH_URL = "https://www.falabella.com/falabella-cl/search?Ntt={query}"

    # Infer clothing type from search query keywords
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
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
                },
            )
        return self._client

    async def search_products(self, query: str, max_items: int = 30) -> list[FalabellaProduct]:
        """Search products via Falabella HTTP search and parse SSR JSON."""
        client = await self._get_client()
        url = self.SEARCH_URL.format(query=query)
        products = []

        # Infer category from query for products missing GSCCategoryId
        inferred_category = self._infer_category(query)

        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            products = self._parse_ssr_data(resp.text, max_items, inferred_category)
        except Exception:
            pass

        return products[:max_items]

    def _infer_category(self, query: str) -> str:
        """Infer frontend category from search query keywords."""
        q = query.lower()
        for keyword, category in self.CATEGORY_KEYWORDS.items():
            if keyword in q:
                return category
        return ""

    async def scrape_category(self, category: str, max_items: int = 50) -> list[FalabellaProduct]:
        """Scrape products from a category using search."""
        return await self.search_products(category, max_items)

    def _parse_ssr_data(self, html: str, max_items: int, inferred_category: str = "") -> list[FalabellaProduct]:
        """Parse Falabella SSR JSON payload to extract products."""
        products = []

        # Find the script tag with props.pageProps.results
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        for s in scripts:
            if not s.startswith('{"props"'):
                continue
            try:
                data = json.loads(s)
                results = data.get("props", {}).get("pageProps", {}).get("results", [])
                if not results:
                    continue

                for item in results[:max_items]:
                    product = self._parse_falabella_product(item, inferred_category)
                    if product and product.name:
                        products.append(product)

                break
            except (json.JSONDecodeError, KeyError):
                continue

        return products[:max_items]

    def _parse_falabella_product(self, item: dict, inferred_category: str = "") -> Optional[FalabellaProduct]:
        """Parse a single Falabella product from SSR data."""
        if not isinstance(item, dict):
            return None

        # Extract fields
        ext_id = str(item.get("productId", ""))
        name = item.get("displayName", "")
        brand = item.get("brand", "")
        url = item.get("url", "")

        # Make URL absolute
        if url and not url.startswith("http"):
            url = f"{self.BASE_URL}{url}"

        # Extract price
        price = 0.0
        prices = item.get("prices", [])
        if isinstance(prices, list) and prices:
            for p in prices:
                if isinstance(p, dict):
                    price_list = p.get("price", [])
                    if isinstance(price_list, list) and price_list:
                        price_str = price_list[0]
                        # Remove dots used as thousand separators
                        price_str = price_str.replace(".", "")
                        try:
                            price = float(price_str)
                            break
                        except ValueError:
                            continue

        # Extract images
        images = []
        media_urls = item.get("mediaUrls", [])
        if isinstance(media_urls, list):
            images = [u for u in media_urls if isinstance(u, str) and u.startswith("http")]

        # Extract category from GSCCategoryId, fallback to inferred from query
        gsc_id = item.get("GSCCategoryId", "")
        category = CATEGORY_MAP.get(gsc_id, "") or inferred_category

        # Extract colors and sizes from variants
        # CORRECT path: variants[type="COLOR"].options[*].sizes[*]["value"]
        colors = []
        sizes = []
        variants = item.get("variants", [])
        if isinstance(variants, list):
            for v in variants:
                if isinstance(v, dict):
                    vtype = v.get("type", "")
                    options = v.get("options", [])
                    if vtype == "COLOR" and isinstance(options, list):
                        # Use "label" for display name, not "value"
                        colors = [
                            o.get("label", o.get("value", "")) for o in options
                            if isinstance(o, dict) and (o.get("label") or o.get("value"))
                        ]
                        # Extract sizes from COLOR options' nested sizes
                        for o in options:
                            if isinstance(o, dict):
                                nested_sizes = o.get("sizes", [])
                                if isinstance(nested_sizes, list):
                                    for ns in nested_sizes:
                                        if isinstance(ns, dict):
                                            size_val = ns.get("value", ns.get("label", ""))
                                            if size_val and size_val not in sizes:
                                                sizes.append(size_val)

        # Extract availability
        availability = True
        avail = item.get("availability", {})
        if isinstance(avail, dict):
            home_del = avail.get("homeDeliveryShipping", "")
            if home_del == "NOT_AVAILABLE":
                availability = False

        if not name:
            return None

        return FalabellaProduct(
            external_id=ext_id,
            name=name,
            price=price,
            currency="CLP",
            image_url=images[0] if images else "",
            category=category,
            sizes=sizes,
            colors=colors,
            description=f"Marca: {brand}" if brand else "",
            availability=availability,
            original_url=url,
        )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
