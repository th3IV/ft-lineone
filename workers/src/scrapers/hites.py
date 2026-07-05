"""Hites scraper — HTTP direct with HTML parsing.

Hites (www.hites.cl) runs on SFCC/Demandware with server-rendered HTML.
Product data is embedded in HTML product cards. Also has JSON-LD structured data.

Endpoint:
  GET https://www.hites.cl/search?q={query}
  GET https://www.hites.cl/{category-path}
"""

import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class HitesProduct:
    """Hites product data."""
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


class HitesScraper:
    """Scraper for Hites (www.hites.cl) using HTTP direct + HTML parsing."""

    BASE_URL = "https://www.hites.cl"
    SEARCH_URL = "https://www.hites.cl/search?q={query}"

    # Map category slugs / keywords to frontend categories
    CATEGORY_KEYWORDS = {
        "polera": "Poleras",
        "camiseta": "Poleras",
        "camisa": "Camisas",
        "blusa": "Camisas",
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
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
                },
            )
        return self._client

    def _infer_category(self, text: str) -> str:
        """Infer frontend category from text."""
        t = text.lower()
        for keyword, category in self.CATEGORY_KEYWORDS.items():
            if keyword in t:
                return category
        return ""

    async def search_products(self, query: str, max_items: int = 30) -> list[HitesProduct]:
        """Search products via Hites search page and parse HTML."""
        client = await self._get_client()
        url = self.SEARCH_URL.format(query=query)
        products = []

        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            products = self._parse_html(resp.text, query, max_items)
        except Exception:
            pass

        return products[:max_items]

    async def scrape_category(self, category: str, max_items: int = 50) -> list[HitesProduct]:
        """Scrape products from a category using search."""
        return await self.search_products(category, max_items)

    def _parse_html(self, html: str, query: str, max_items: int) -> list[HitesProduct]:
        """Parse Hites HTML to extract products."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        products = []
        seen_ids = set()

        # Try multiple selectors for product cards
        selectors = [
            ".product-tile",
            ".product-card",
            "[data-pid]",
            ".product-grid .product",
            ".search-results .product",
        ]

        items = []
        for sel in selectors:
            items = soup.select(sel)
            if items:
                break

        # Also try to extract from JSON-LD
        json_ld_products = self._extract_json_ld(soup)
        if json_ld_products:
            for p in json_ld_products:
                if len(products) >= max_items:
                    break
                pid = p.get("sku", "")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    products.append(p)

        # Parse product cards from HTML
        for item in items[:max_items]:
            if len(products) >= max_items:
                break
            try:
                product = self._parse_product_card(item, query)
                if product and product.name and product.external_id not in seen_ids:
                    seen_ids.add(product.external_id)
                    products.append(product)
            except Exception:
                continue

        return products[:max_items]

    def _extract_json_ld(self, soup) -> list[HitesProduct]:
        """Extract products from JSON-LD structured data."""
        products = []
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                import json
                data = json.loads(script.string or "")
                if isinstance(data, dict) and data.get("@type") == "ItemList":
                    for list_item in data.get("itemListElement", []):
                        item = list_item.get("item", {})
                        if item.get("@type") == "Product":
                            product = self._parse_json_ld_product(item)
                            if product:
                                products.append(product)
                elif isinstance(data, dict) and data.get("@type") == "Product":
                    product = self._parse_json_ld_product(data)
                    if product:
                        products.append(product)
            except (json.JSONDecodeError, AttributeError):
                continue
        return products

    def _parse_json_ld_product(self, item: dict) -> Optional[HitesProduct]:
        """Parse a product from JSON-LD data."""
        name = item.get("name", "")
        if not name:
            return None

        sku = item.get("sku", "")
        url = item.get("url", "")
        image = item.get("image", "")
        brand = ""
        brand_data = item.get("brand", {})
        if isinstance(brand_data, dict):
            brand = brand_data.get("name", "")

        # Price from offers
        price = 0.0
        offers = item.get("offers", {})
        if isinstance(offers, dict):
            try:
                price = float(offers.get("price", 0))
            except (ValueError, TypeError):
                pass
        elif isinstance(offers, list) and offers:
            try:
                price = float(offers[0].get("price", 0))
            except (ValueError, TypeError):
                pass

        # Availability
        availability = True
        if isinstance(offers, dict):
            avail_url = offers.get("availability", "")
            if "OutOfStock" in str(avail_url):
                availability = False

        category = self._infer_category(name)

        return HitesProduct(
            external_id=str(sku) if sku else "",
            name=name,
            price=price,
            currency="CLP",
            image_url=image if isinstance(image, str) else (image[0] if isinstance(image, list) and image else ""),
            category=category,
            sizes=[],
            colors=[],
            description=f"Marca: {brand}" if brand else "",
            availability=availability,
            original_url=url,
        )

    def _parse_product_card(self, item, query: str) -> Optional[HitesProduct]:
        """Parse a product from HTML product card."""
        import re

        # Product name
        name = ""
        name_selectors = [
            ".product-tile__name",
            ".product-name",
            ".product-card__title",
            "[class*='product-name']",
            "[class*='product-title']",
            "h3",
            "h2",
        ]
        for sel in name_selectors:
            elem = item.select_one(sel)
            if elem:
                name = elem.get_text(strip=True)
                if name:
                    break

        if not name:
            return None

        # Product ID
        product_id = item.get("data-pid", "") or item.get("data-product-id", "")
        if not product_id:
            # Extract from URL
            link = item.select_one("a[href]")
            if link:
                href = link.get("href", "")
                match = re.search(r"/p/(\d+)", href)
                if match:
                    product_id = match.group(1)
                else:
                    match = re.search(r"/(\d+)\.html", href)
                    if match:
                        product_id = match.group(1)

        if not product_id:
            product_id = re.sub(r"[^a-z0-9]", "-", name.lower())[:50]

        # Price
        price = 0.0
        price_selectors = [
            ".price .sales .value",
            ".price-sales",
            ".price",
            "[class*='price'] .value",
            "[class*='price']",
        ]
        for sel in price_selectors:
            elem = item.select_one(sel)
            if elem:
                price_text = elem.get_text(strip=True)
                if price_text:
                    price = self._normalize_price(price_text)
                    if price > 0:
                        break

        # Image
        image_url = ""
        img = item.select_one("img")
        if img:
            image_url = img.get("src", "") or img.get("data-src", "")
            if image_url and not image_url.startswith("http"):
                image_url = f"{self.BASE_URL}{image_url}"

        # Product URL
        original_url = ""
        link = item.select_one("a[href]")
        if link:
            href = link.get("href", "")
            if href.startswith("http"):
                original_url = href
            elif href.startswith("/"):
                original_url = f"{self.BASE_URL}{href}"

        # Category
        category = self._infer_category(name) or self._infer_category(query)

        return HitesProduct(
            external_id=product_id,
            name=name,
            price=price,
            currency="CLP",
            image_url=image_url,
            category=category,
            sizes=[],
            colors=[],
            description="",
            availability=True,
            original_url=original_url,
        )

    def _normalize_price(self, price_str: str) -> float:
        """Normalize Chilean price string to float."""
        cleaned = re.sub(r"[^\d.,]", "", price_str)
        if "." in cleaned and "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "." in cleaned:
            parts = cleaned.split(".")
            if len(parts) > 2:
                cleaned = cleaned.replace(".", "")
            elif len(parts[-1]) == 3:
                cleaned = cleaned.replace(".", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
