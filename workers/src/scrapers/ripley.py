"""Ripley scraper — HTTP direct with HTML parsing.

Ripley Chile (simple.ripley.cl) uses Cloudflare protection.
We try to access the search page and parse product data from the HTML.

Workflow:
  1. GET /search?term={query}
  2. Parse HTML for product data
"""

import json
import re
from typing import Optional
from dataclasses import dataclass, field

import js
from pyodide.ffi import to_js as _to_js
from js import Object


def to_js(obj):
    """Convert Python objects to JS with dict_converter."""
    return _to_js(obj, dict_converter=Object.fromEntries)


@dataclass
class RipleyProduct:
    """Ripley product data."""
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


class RipleyScraper:
    """Scraper for Ripley (simple.ripley.cl) using HTTP direct + HTML parsing."""

    BASE_URL = "https://simple.ripley.cl"
    SEARCH_URL = "https://simple.ripley.cl/search?term={query}"

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

    def _parse_html_products(self, html: str, query: str, max_items: int) -> list[RipleyProduct]:
        """Parse product data from Ripley HTML."""
        products = []
        seen_ids = set()

        category = self._infer_category(query)
        gender = self._infer_gender(query)
        display_category = f"{category} {gender}".strip() if category else query

        # Try to find product data in JSON-LD scripts
        json_ld_pattern = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL)
        for match in json_ld_pattern.finditer(html):
            try:
                data = json.loads(match.group(1))
                if isinstance(data, dict) and data.get("@type") == "Product":
                    product = self._parse_json_ld_product(data, display_category)
                    if product and product.external_id not in seen_ids:
                        seen_ids.add(product.external_id)
                        products.append(product)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "Product":
                            product = self._parse_json_ld_product(item, display_category)
                            if product and product.external_id not in seen_ids:
                                seen_ids.add(product.external_id)
                                products.append(product)
            except (json.JSONDecodeError, Exception):
                continue

        # Try to find product data in script tags with JSON
        script_pattern = re.compile(r'<script[^>]*>(.*?)</script>', re.DOTALL)
        for match in script_pattern.finditer(html):
            script_content = match.group(1)
            # Look for product arrays in JSON
            if '"products"' in script_content or '"items"' in script_content:
                try:
                    # Try to extract JSON from script
                    json_match = re.search(r'(\{[^{}]*"products"\s*:\s*\[.*?\]\s*\})', script_content, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group(1))
                        items = data.get("products", data.get("items", []))
                        for item in items:
                            if isinstance(item, dict):
                                product = self._parse_json_product(item, display_category)
                                if product and product.external_id not in seen_ids:
                                    seen_ids.add(product.external_id)
                                    products.append(product)
                except (json.JSONDecodeError, Exception):
                    continue

        # Try to find product data in data attributes
        data_pattern = re.compile(r'data-product[^=]*="([^"]*)"')
        for match in data_pattern.finditer(html):
            try:
                data = json.loads(match.group(1).replace('&quot;', '"'))
                if isinstance(data, dict):
                    product = self._parse_json_product(data, display_category)
                    if product and product.external_id not in seen_ids:
                        seen_ids.add(product.external_id)
                        products.append(product)
            except (json.JSONDecodeError, Exception):
                continue

        return products[:max_items]

    def _parse_json_ld_product(self, data: dict, category: str) -> Optional[RipleyProduct]:
        """Parse a product from JSON-LD data."""
        try:
            name = data.get("name", "")
            if not name:
                return None

            external_id = data.get("sku", "") or data.get("mpn", "") or ""
            if not external_id:
                return None

            # Price
            price = 0.0
            offers = data.get("offers", {})
            if isinstance(offers, dict):
                price_val = offers.get("price", 0) or offers.get("lowPrice", 0)
                try:
                    price = float(price_val)
                except (ValueError, TypeError):
                    pass

            # Image
            image = data.get("image", "")
            if isinstance(image, list):
                image = image[0] if image else ""

            # URL
            url = data.get("url", "")
            if url and not url.startswith("http"):
                url = f"{self.BASE_URL}{url}"

            return RipleyProduct(
                external_id=str(external_id),
                name=name,
                price=price,
                currency="CLP",
                image_url=image,
                category=category,
                sizes=[],
                colors=[],
                description=data.get("description", ""),
                availability=True,
                original_url=url,
                image_urls=[image] if image else [],
            )
        except Exception:
            return None

    def _parse_json_product(self, data: dict, category: str) -> Optional[RipleyProduct]:
        """Parse a product from JSON data."""
        try:
            name = data.get("name", "") or data.get("title", "") or data.get("productName", "")
            if not name:
                return None

            external_id = str(data.get("id", "") or data.get("productId", "") or data.get("sku", ""))
            if not external_id:
                return None

            # Price
            price = 0.0
            price_val = data.get("price", 0) or data.get("salePrice", 0) or data.get("offerPrice", 0)
            try:
                price = float(price_val)
            except (ValueError, TypeError):
                pass

            # Image
            image = data.get("image", "") or data.get("imageUrl", "") or data.get("thumbnail", "")
            if isinstance(image, list):
                image = image[0] if image else ""

            # URL
            url = data.get("url", "") or data.get("link", "") or data.get("productUrl", "")
            if url and not url.startswith("http"):
                url = f"{self.BASE_URL}{url}"

            # Images
            image_urls = []
            images = data.get("images", []) or data.get("imageUrls", [])
            if isinstance(images, list):
                for img in images:
                    if isinstance(img, str) and img.startswith("http"):
                        image_urls.append(img)
                    elif isinstance(img, dict):
                        img_url = img.get("url", "") or img.get("imageUrl", "")
                        if img_url:
                            image_urls.append(img_url)

            return RipleyProduct(
                external_id=external_id,
                name=name,
                price=price,
                currency="CLP",
                image_url=image,
                category=category,
                sizes=[],
                colors=[],
                description=data.get("description", ""),
                availability=True,
                original_url=url,
                image_urls=image_urls if image_urls else ([image] if image else []),
            )
        except Exception:
            return None

    async def search_products(self, query: str, max_items: int = 30) -> list[RipleyProduct]:
        """Search products via Ripley HTTP search."""
        products = []

        try:
            url = self.SEARCH_URL.format(query=query)
            print(json.dumps({"event": "ripley_search_request", "query": query, "url": url}))

            resp = await js.fetch(url, to_js({
                "method": "GET",
                "headers": {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
                },
            }))

            print(json.dumps({"event": "ripley_search_response", "ok": resp.ok, "status": resp.status}))

            if not resp.ok:
                error_text = await resp.text()
                print(json.dumps({"event": "ripley_search_error", "query": query, "status": resp.status, "error": error_text[:500]}))
                return []

            html = await resp.text()
            print(json.dumps({"event": "ripley_search_html", "query": query, "length": len(html)}))

            products = self._parse_html_products(html, query, max_items)
            print(json.dumps({"event": "ripley_search_success", "query": query, "products_found": len(products)}))

        except Exception as e:
            print(json.dumps({"event": "ripley_search_error", "query": query, "error": str(e)}))

        return products[:max_items]

    async def scrape_category(self, category: str, max_items: int = 50) -> list[RipleyProduct]:
        """Scrape products from a category using search."""
        return await self.search_products(category, max_items)

    async def close(self):
        """No-op for js.fetch (no client to close)."""
        pass
