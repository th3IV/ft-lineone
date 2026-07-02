"""Paris scraper - Constructor.io search API + HTML fallback."""

import re
import httpx
from bs4 import BeautifulSoup
from typing import Optional
from dataclasses import dataclass


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


class ParisScraper:
    """Scraper for Paris (paris.cl) using Constructor.io search API."""

    BASE_URL = "https://www.paris.cl"
    # Constructor.io API key from page source
    CNSTRC_JS = "https://cnstrc.com/js/cust/cencosud_0BmS-e.js"
    CNSTRC_API = "https://ac.cnstrc.com/search"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "es-CL,es;q=0.9",
                "Origin": "https://www.paris.cl",
                "Referer": "https://www.paris.cl/",
            },
        )
        self._cnstrc_key: Optional[str] = None

    async def _get_cnstrc_key(self) -> str:
        """Extract Constructor.io API key from JS bundle."""
        if self._cnstrc_key:
            return self._cnstrc_key
        # Try known Constructor.io key patterns for paris.cl
        try:
            resp = await self.client.get(self.CNSTRC_JS)
            if resp.status_code == 200:
                # Look for key in format: "key":"xxxxxxxxxx" or key='xxxxxxxxxx'
                matches = re.findall(r'"key"\s*:\s*"([a-zA-Z0-9_-]{20,})"', resp.text)
                if matches:
                    self._cnstrc_key = matches[0]
                    return self._cnstrc_key
                # Alternative pattern
                matches = re.findall(r"key[=:]['\"]?([a-zA-Z0-9]{32,})['\"]?", resp.text)
                if matches:
                    self._cnstrc_key = matches[0]
                    return self._cnstrc_key
        except Exception:
            pass
        # Fallback: try page source for cnstrc key
        try:
            resp = await self.client.get(self.BASE_URL)
            if resp.status_code == 200:
                match = re.search(r'cnstrc[^"\']*(?:key|token)[=:\'"]\s*([a-zA-Z0-9_-]{20,})', resp.text)
                if match:
                    self._cnstrc_key = match.group(1)
                    return self._cnstrc_key
        except Exception:
            pass
        return ""

    async def search_products(self, query: str, max_items: int = 30) -> list[ParisProduct]:
        """Search products via Constructor.io API."""
        key = await self._get_cnstrc_key()
        if not key:
            return await self._search_html_fallback(query, max_items)

        try:
            resp = await self.client.get(
                self.CNSTRC_API,
                params={
                    "key": key,
                    "i": query,
                    "num_results_per_page": min(max_items, 50),
                    "section": "Products",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("response", {}).get("results", [])
            return [self._parse_cnstrc(r) for r in results[:max_items]]
        except Exception:
            return await self._search_html_fallback(query, max_items)

    async def scrape_category(self, category: str, max_items: int = 50) -> list[ParisProduct]:
        """Scrape products from a category using search."""
        return await self.search_products(category, max_items)

    async def _search_html_fallback(self, query: str, max_items: int) -> list[ParisProduct]:
        """Fallback: fetch search page and parse HTML."""
        products = []
        try:
            resp = await self.client.get(
                f"{self.BASE_URL}/search",
                params={"q": query},
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract __NEXT_DATA__ for product data
            next_data = soup.select_one("script#__NEXT_DATA__")
            if next_data:
                import json
                data = json.loads(next_data.string)
                props = data.get("props", {}).get("pageProps", {})
                items = props.get("products", props.get("items", []))
                for item in items[:max_items]:
                    product = self._parse_next_data(item)
                    if product:
                        products.append(product)
        except Exception:
            pass
        return products

    def _parse_cnstrc(self, result: dict) -> ParisProduct:
        """Parse Constructor.io search result."""
        data = result.get("data", {})
        value = result.get("value", "")
        id_ = result.get("id", "")

        # Extract product URL
        product_url = data.get("url", "")
        if not product_url and id_:
            product_url = f"{self.BASE_URL}/{id_}"

        # Extract image
        image_url = data.get("image_url", "")
        if not image_url:
            image_url = data.get("img", "")

        # Extract price
        price = 0.0
        price_data = data.get("price", 0)
        if isinstance(price_data, (int, float)):
            price = float(price_data)
        elif isinstance(price_data, str):
            price = self._normalize_price(price_data)

        # Check for sale price
        sale_price = data.get("sale_price", 0)
        if isinstance(sale_price, (int, float)) and sale_price > 0:
            price = float(sale_price)

        # Extract availability
        availability = True
        if "out_of_stock" in str(data).lower():
            availability = False

        return ParisProduct(
            external_id=str(id_),
            name=value or data.get("name", ""),
            price=price,
            currency="CLP",
            image_url=image_url,
            category=data.get("category", ""),
            sizes=data.get("sizes", []),
            colors=data.get("colors", []),
            description=data.get("description", ""),
            availability=availability,
            original_url=product_url,
        )

    def _parse_next_data(self, item: dict) -> Optional[ParisProduct]:
        """Parse product from __NEXT_DATA__."""
        name = item.get("name", item.get("title", ""))
        if not name:
            return None

        product_id = str(item.get("id", item.get("productId", "")))
        price = float(item.get("price", item.get("salePrice", 0)) or 0)
        image_url = item.get("imageUrl", item.get("image", ""))
        if isinstance(image_url, list) and image_url:
            image_url = image_url[0]

        return ParisProduct(
            external_id=product_id,
            name=name,
            price=price,
            currency="CLP",
            image_url=image_url,
            category=item.get("category", ""),
            sizes=item.get("sizes", []),
            colors=item.get("colors", []),
            description=item.get("description", ""),
            availability=item.get("availability", True),
            original_url=item.get("url", f"{self.BASE_URL}/product/{product_id}"),
        )

    def _normalize_price(self, price_str: str) -> float:
        """Normalize price string to float."""
        cleaned = re.sub(r"[^\d.,]", "", price_str)
        cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
