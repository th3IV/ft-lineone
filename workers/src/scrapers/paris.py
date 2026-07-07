"""Paris scraper — HTTP direct with RSC/LD+JSON extraction.

Paris.cl renders products via React Server Components. Product data is
embedded in the HTML as serialized RSC payload inside <script> tags.
LD+JSON structured data is embedded inside RSC push scripts with escaped quotes.

Workflow:
  1. GET /search?q={query}
  2. Find RSC push scripts containing itemListElement (product list)
  3. Unescape the JSON and parse LD+JSON product data
"""

import asyncio
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
    """Scraper for Paris (paris.cl) using HTTP direct + RSC/LD+JSON."""

    BASE_URL = "https://www.paris.cl"
    SEARCH_URL = "https://www.paris.cl/search?q={query}"

    # Category keywords for mapping search queries → frontend categories
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

    def _extract_sizes_from_html(self, html: str) -> list[str]:
        """Best-effort size extraction from a Paris product detail page."""
        sizes = []
        if not html:
            return sizes

        patterns = [
            r'\\"name\\":\\"size\\",\\"value\\":\\"([^"\\]+)\\"',
            r'"size"\s*:\s*\{[^}]*"value"\s*:\s*"([^"]+)"',
            r'"sizes"\s*:\s*(\[[^\]]+\])',
            r'"tallas"\s*:\s*(\[[^\]]+\])',
            r'"Talla\s+([A-Z0-9]+)"',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html)
            for m in matches:
                if isinstance(m, tuple):
                    m = m[0]
                if m.startswith("["):
                    try:
                        arr = json.loads(m)
                        for val in arr:
                            if isinstance(val, str) and val and val not in sizes:
                                sizes.append(val)
                    except json.JSONDecodeError:
                        continue
                elif m and m not in sizes:
                    sizes.append(m)

        return sizes

    def _extract_colors_from_html(self, html: str) -> list[str]:
        """Best-effort color extraction from a Paris product detail page."""
        colors = []
        if not html:
            return colors

        patterns = [
            r'\\"name\\":\\"color\\",\\"value\\":\\"([^"\\]+)\\"',
            r'"color"\s*:\s*\{[^}]*"value"\s*:\s*"([^"]+)"',
            r'"colors"\s*:\s*(\[[^\]]+\])',
            r'"colores"\s*:\s*(\[[^\]]+\])',
            r'"Color\s+([A-Za-záéíóúÁÉÍÓÚñÑ]+)"',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html)
            for m in matches:
                if isinstance(m, tuple):
                    m = m[0]
                if m.startswith("["):
                    try:
                        arr = json.loads(m)
                        for val in arr:
                            if isinstance(val, str) and val and val not in colors:
                                colors.append(val)
                    except json.JSONDecodeError:
                        continue
                elif m and m not in colors:
                    colors.append(m)

        return colors

    async def _fetch_product_details(self, client, url: str) -> tuple[list[str], list[str]]:
        """Fetch product detail page and extract sizes and colors."""
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                return (
                    self._extract_sizes_from_html(resp.text),
                    self._extract_colors_from_html(resp.text),
                )
        except Exception as e:
                print(json.dumps({"event": "paris_detail_error", "url": url, "error": str(e)}))
        return [], []

    async def _enrich_with_details(self, client, products: list[ParisProduct]) -> None:
        """Enrich products with sizes and colors from their detail pages in parallel."""
        tasks = [self._fetch_product_details(client, p.original_url) for p in products if p.original_url]
        results = await asyncio.gather(*tasks)
        for product, (sizes, colors) in zip(products, results):
            if sizes:
                product.sizes = sizes
            if colors:
                product.colors = colors

    async def search_products(self, query: str, max_items: int = 30) -> list[ParisProduct]:
        """Search products via Paris.cl HTTP search and parse RSC/LD+JSON."""
        client = await self._get_client()
        url = self.SEARCH_URL.format(query=query)
        products = []

        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                print(json.dumps({"event": "paris_search_error", "query": query, "status": resp.status_code}))
                return []
            products = self._parse_ssr_data(resp.text, query, max_items)
            # Best-effort size and color enrichment from product detail pages
            if products:
                await self._enrich_with_details(client, products)
            print(json.dumps({"event": "paris_search_success", "query": query, "products_found": len(products)}))
        except Exception as e:
            print(json.dumps({"event": "paris_search_error", "query": query, "error": str(e)}))

        return products[:max_items]

    async def scrape_category(self, category: str, max_items: int = 50) -> list[ParisProduct]:
        """Scrape products from a category using search."""
        return await self.search_products(category, max_items)

    def _parse_ssr_data(self, html: str, query: str, max_items: int) -> list[ParisProduct]:
        """Parse Paris.cl SSR RSC payload to extract products."""
        products = []
        seen_ids = set()

        category = self._infer_category(query)
        gender = self._infer_gender(query)
        display_category = f"{category} {gender}".strip() if category else query

        # Find RSC push scripts containing itemListElement
        scripts = re.findall(
            r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', html, re.DOTALL
        )

        for script in scripts:
            if "itemListElement" not in script:
                continue

            try:
                # Find the JSON start (first {)
                json_start = script.find("{")
                if json_start < 0:
                    continue

                raw = script[json_start:]

                # Unescape the content
                content = raw.replace('\\"', '"')
                content = content.replace("\\/", "/")
                content = content.replace("\\\\", "\\")

                # Parse the JSON
                data = json.loads(content)

                # Navigate to itemListElement
                items = data.get("mainEntity", {}).get("itemListElement", [])
                for item in items:
                    if len(products) >= max_items:
                        break

                    product_data = item.get("item", {})
                    if not product_data or product_data.get("@type") != "Product":
                        continue

                    name = product_data.get("name", "")
                    url = product_data.get("url", "")
                    image = product_data.get("image", "")
                    sku = product_data.get("sku", "")

                    if not name:
                        continue

                    # Deduplicate by SKU or URL
                    dedup_key = sku or url
                    if dedup_key in seen_ids:
                        continue
                    seen_ids.add(dedup_key)

                    # Extract price and availability from offers
                    price = 0.0
                    availability = True
                    offers = product_data.get("offers", {})
                    if isinstance(offers, dict):
                        price_val = offers.get("price", 0)
                        try:
                            price = float(price_val)
                        except (ValueError, TypeError):
                            pass
                        avail_url = str(offers.get("availability", ""))
                        if "OutOfStock" in avail_url or "out_of_stock" in avail_url.lower():
                            availability = False

                    # Extract images
                    image = product_data.get("image", "")
                    image_urls = []
                    if isinstance(image, str) and image:
                        image_urls.append(image)
                    elif isinstance(image, list):
                        for img in image:
                            if isinstance(img, str) and img and img not in image_urls:
                                image_urls.append(img)

                    # Extract brand
                    brand = ""
                    brand_data = product_data.get("brand", {})
                    if isinstance(brand_data, dict):
                        brand = brand_data.get("name", "")

                    products.append(ParisProduct(
                        external_id=str(sku) if sku else str(len(products)),
                        name=name,
                        price=price,
                        currency="CLP",
                        image_url=image_urls[0] if image_urls else "",
                        category=display_category,
                        sizes=[],
                        colors=[],
                        description=f"Marca: {brand}" if brand else "",
                        availability=availability,
                        original_url=url,
                        image_urls=image_urls,
                    ))

                break  # Found the product list, no need to continue

            except (json.JSONDecodeError, KeyError):
                continue

        return products

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
