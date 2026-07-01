"""Paris scraper using BeautifulSoup (HTTP-based)."""

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
    """Scraper for Paris (paris.cl) - HTTP-based, no browser needed."""

    BASE_URL = "https://www.paris.cl"

    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "es-CL,es;q=0.9",
            },
        )

    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object."""
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except Exception:
            return None

    def scrape_category(
        self, category: str, max_items: int = 50
    ) -> list[ParisProduct]:
        """Scrape products from a category page."""
        products = []
        url = f"{self.BASE_URL}/catalogo/{category}"

        soup = self.get_page(url)
        if not soup:
            return products

        # Try multiple selectors (Paris might use different layouts)
        items = (
            soup.select(".producto")
            or soup.select(".product-item")
            or soup.select("[data-product-id]")
            or soup.select(".product-card")
        )

        for item in items[:max_items]:
            try:
                product = self._parse_product(item, category)
                if product:
                    products.append(product)
            except Exception:
                continue

        return products

    def search_products(
        self, query: str, max_items: int = 30
    ) -> list[ParisProduct]:
        """Search products by keyword."""
        products = []
        url = f"{self.BASE_URL}/search?q={query}"

        soup = self.get_page(url)
        if not soup:
            return products

        items = (
            soup.select(".product-item")
            or soup.select(".search-result-item")
            or soup.select("[data-product-id]")
        )

        for item in items[:max_items]:
            try:
                product = self._parse_product(item, "search")
                if product:
                    products.append(product)
            except Exception:
                continue

        return products

    def _parse_product(self, item: BeautifulSoup, category: str) -> Optional[ParisProduct]:
        """Parse a product item from the page."""
        # Get name
        name = ""
        name_elem = (
            item.select_one(".product-title a")
            or item.select_one(".product-name")
            or item.select_one("h2")
            or item.select_one("h3")
        )
        if name_elem:
            name = name_elem.get_text(strip=True)

        if not name:
            return None

        # Get price
        price = 0.0
        price_elem = (
            item.select_one(".product-price .price")
            or item.select_one("[data-price-value]")
            or item.select_one(".price-current")
        )
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price = self._normalize_price(price_text)

        # Get product ID
        product_id = ""
        id_elem = item.select_one("[data-id]") or item.select_one("[data-product-id]")
        if id_elem:
            product_id = id_elem.get("data-id") or id_elem.get("data-product-id", "")

        if not product_id:
            # Generate from name
            product_id = re.sub(r'[^a-z0-9]', '-', name.lower())[:50]

        # Get image
        image_url = ""
        img_elem = (
            item.select_one(".product-image img")
            or item.select_one("img[src]")
            or item.select_one("img[data-src]")
        )
        if img_elem:
            image_url = img_elem.get("src") or img_elem.get("data-src", "")

        # Get sizes
        sizes = []
        size_elems = item.select(".size-variant, .size-option, .size-selector button")
        for s in size_elems:
            text = s.get_text(strip=True)
            if text and text not in sizes:
                sizes.append(text)

        # Get colors
        colors = []
        color_elems = item.select(".color-variant, .color-option, .color-selector span")
        for c in color_elems:
            text = c.get_text(strip=True)
            if text and text not in colors:
                colors.append(text)

        # Get availability
        availability = True
        stock_elem = item.select_one(".stock-status, .availability")
        if stock_elem:
            stock_text = stock_elem.get_text(strip=True).lower()
            availability = "out" not in stock_text and "agotado" not in stock_text

        # Build original URL
        link_elem = item.select_one("a[href]")
        original_url = ""
        if link_elem:
            href = link_elem.get("href", "")
            if href.startswith("http"):
                original_url = href
            elif href.startswith("/"):
                original_url = f"{self.BASE_URL}{href}"

        return ParisProduct(
            external_id=product_id,
            name=name,
            price=price,
            currency="CLP",
            image_url=image_url,
            category=category,
            sizes=sizes,
            colors=colors,
            description="",
            availability=availability,
            original_url=original_url,
        )

    def _normalize_price(self, price_str: str) -> float:
        """Normalize price string to float."""
        cleaned = re.sub(r'[^\d.,]', '', price_str)
        cleaned = cleaned.replace('.', '').replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def close(self):
        """Close the HTTP client."""
        self.client.close()
