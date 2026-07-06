"""Fashion Park scraper — Shopify JSON API.

Fashion Park (fashionspark.com) runs on Shopify, which exposes public JSON
endpoints. No bot detection, no auth required.

Endpoints:
  GET /search/suggest.json?q={query}&resources[type]=product&resources[limit]=30
  GET /collections/{handle}/products.json?limit=250&page=1
  GET /collections/all/products.json?limit=250&page=N
"""

import asyncio
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
    image_urls: list[str] = field(default_factory=list)


class FashionParkScraper:
    """Scraper for Fashion Park (fashionspark.com) using Shopify JSON API."""

    BASE_URL = "https://fashionspark.com"
    SEARCH_URL = "https://fashionspark.com/search/suggest.json?q={query}&resources[type]=product&resources[limit]=30"
    COLLECTION_URL = "https://fashionspark.com/collections/all/products.json?limit=250&page={page}"
    PRODUCT_URL = "https://fashionspark.com/products/{handle}.json"

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

    def _extract_sizes_from_variants(self, product_data: dict) -> list[str]:
        """Extract sizes from Shopify product variants/options."""
        sizes = []
        product = product_data.get("product", {})
        options = product.get("options", [])
        variants = product.get("variants", [])

        # Find the size option name
        size_option_index = None
        for idx, opt in enumerate(options):
            opt_name = (opt.get("name") or "").lower()
            if "size" in opt_name or "talla" in opt_name:
                size_option_index = idx
                break

        if size_option_index is not None and variants:
            key = f"option{size_option_index + 1}"
            for v in variants:
                val = v.get(key, "")
                if val and val not in sizes:
                    sizes.append(val)
        elif variants:
            for v in variants:
                title = v.get("title", "")
                if " - " in title:
                    val = title.split(" - ")[-1].strip()
                    if val and val not in sizes:
                        sizes.append(val)

        return sizes

    def _extract_colors_from_variants(self, product_data: dict) -> list[str]:
        """Extract colors from Shopify product variants/options."""
        colors = []
        product = product_data.get("product", {})
        options = product.get("options", [])
        variants = product.get("variants", [])

        color_option_index = None
        for idx, opt in enumerate(options):
            opt_name = (opt.get("name") or "").lower()
            if "color" in opt_name or "colour" in opt_name:
                color_option_index = idx
                break

        if color_option_index is not None and variants:
            key = f"option{color_option_index + 1}"
            for v in variants:
                val = v.get(key, "")
                if val and val not in colors:
                    colors.append(val)

        return colors

    def _extract_image_urls(self, product_data: dict) -> list[str]:
        """Extract all image URLs from Shopify product detail."""
        product = product_data.get("product", {})
        images = product.get("images", [])
        urls = []
        for img in images:
            if isinstance(img, dict):
                src = img.get("src", "")
                if src and src not in urls:
                    urls.append(src)
            elif isinstance(img, str) and img and img not in urls:
                urls.append(img)
        return urls

    async def _fetch_product_detail(self, client, handle: str) -> dict:
        """Fetch product detail JSON from Shopify."""
        try:
            url = self.PRODUCT_URL.format(handle=handle)
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"[fashionpark] Error fetching detail for {handle}: {e}")
        return {}

    async def _enrich_with_details(self, client, items: list[dict]) -> dict[str, dict]:
        """Fetch product details and return a handle->{sizes, colors, image_urls} mapping."""
        handles = [item.get("handle", "") for item in items if item.get("handle")]
        results = await asyncio.gather(*[self._fetch_product_detail(client, h) for h in handles])
        mapping = {}
        for item, detail in zip(items, results):
            handle = item.get("handle", "")
            if handle and detail:
                mapping[handle] = {
                    "sizes": self._extract_sizes_from_variants(detail),
                    "colors": self._extract_colors_from_variants(detail),
                    "image_urls": self._extract_image_urls(detail),
                }
        return mapping

    async def search_products(self, query: str, max_items: int = 30) -> list[FashionParkProduct]:
        """Search products via Fashion Park Shopify suggest API."""
        client = await self._get_client()
        url = self.SEARCH_URL.format(query=query)
        products = []

        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                print(f"[fashionpark] Search '{query}' returned status {resp.status_code}")
                return []
            data = resp.json()
            results = data.get("resources", {}).get("results", {}).get("products", [])

            # Fetch sizes, colors and images from product detail JSON in parallel
            details_map = await self._enrich_with_details(client, results[:max_items])

            for item in results[:max_items]:
                handle = item.get("handle", "")
                details = details_map.get(handle, {})
                product = self._parse_suggest_product(
                    item,
                    query,
                    sizes=details.get("sizes", []),
                    colors=details.get("colors", []),
                    image_urls=details.get("image_urls", []),
                )
                if product and product.name:
                    products.append(product)
            print(f"[fashionpark] Search '{query}' parsed {len(products)} products")
        except Exception as e:
            print(f"[fashionpark] Error searching '{query}': {type(e).__name__}: {e}")

        return products[:max_items]

    async def scrape_category(self, category: str, max_items: int = 50) -> list[FashionParkProduct]:
        """Scrape products from a category using search."""
        return await self.search_products(category, max_items)

    def _parse_suggest_product(self, item: dict, query: str, sizes: list[str] = None, colors: list[str] = None, image_urls: list[str] = None) -> Optional[FashionParkProduct]:
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

        # Image (primary from suggest, override if detail images available)
        image_url = ""
        featured = item.get("featured_image")
        if isinstance(featured, dict):
            image_url = featured.get("url", "")
        elif isinstance(featured, str):
            image_url = featured

        all_image_urls = image_urls if image_urls else ([image_url] if image_url else [])
        if image_url and image_urls and image_url not in image_urls:
            all_image_urls = [image_url] + image_urls
        elif not all_image_urls and image_url:
            all_image_urls = [image_url]

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

        return FashionParkProduct(
            external_id=product_id,
            name=title,
            price=price,
            currency="CLP",
            image_url=all_image_urls[0] if all_image_urls else "",
            category=display_category,
            sizes=sizes or [],
            colors=colors or [],
            description=f"Tipo: {product_type}" if product_type else "",
            availability=availability,
            original_url=original_url,
            image_urls=all_image_urls,
        )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
