"""Maui scraper - Magento 2 HTTP direct scraping.

Maui & Sons Chile uses Magento 2. All CSS selectors verified:
  .product-item-info, .product-item-link, .price-box .price,
  [data-price-amount], .product-image-photo, [data-product-id],
  .swatch-option.text[data-option-label]
"""

import re
import httpx
from bs4 import BeautifulSoup
from typing import Optional
from dataclasses import dataclass


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


class MauiScraper:
    """Scraper for Maui & Sons (mauiandsons.cl) - Magento 2 platform."""

    BASE_URL = "https://mauiandsons.cl"

    # Magento 2 category paths → frontend category mapping
    CATEGORY_PATHS = {
        # Poleras
        "hombre-poleras": "/hombre/vestuario/poleras.html",
        "mujer-poleras": "/mujer/vestuario/poleras.html",
        # Camisas
        "hombre-camisas": "/hombre/vestuario/camisas.html",
        "mujer-camisas": "/mujer/vestuario/camisas.html",
        # Pantalones
        "hombre-pantalones": "/hombre/vestuario/pantalones.html",
        "mujer-pantalones": "/mujer/vestuario/pantalones.html",
        # Jeans
        "hombre-jeans": "/hombre/vestuario/jeans.html",
        "mujer-jeans": "/mujer/vestuario/jeans.html",
        # Shorts
        "hombre-shorts": "/hombre/vestuario/shorts.html",
        "mujer-shorts": "/mujer/vestuario/shorts.html",
        # Chaquetas / Parkas
        "hombre-chaquetas": "/hombre/vestuario/parkas-y-chaquetas.html",
        "mujer-chaquetas": "/mujer/vestuario/parkas-y-chaquetas.html",
        # Vestidos
        "mujer-vestidos": "/mujer/vestuario/vestidos.html",
        # Faldas
        "mujer-faldas": "/mujer/vestuario/faldas.html",
        # Polerones / Buzos
        "hombre-polerones": "/hombre/vestuario/polerones.html",
        "mujer-polerones": "/mujer/vestuario/polerones.html",
    }

    # Map internal slugs to frontend categories
    CATEGORY_MAP = {
        "poleras": "Poleras",
        "camisas": "Camisas",
        "pantalones": "Pantalones",
        "jeans": "Pantalones",
        "shorts": "Shorts",
        "chaquetas": "Chaquetas",
        "parkas": "Chaquetas",
        "vestidos": "Vestidos",
        "faldas": "Faldas",
        "polerones": "Polerones",
        "buzos": "Polerones",
    }

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
            },
        )

    def _infer_gender(self, path: str) -> str:
        """Infer gender from URL path."""
        if "/hombre/" in path:
            return "hombre"
        elif "/mujer/" in path:
            return "mujer"
        return ""

    def _map_category(self, slug: str) -> str:
        """Map internal slug to frontend category."""
        for key, category in self.CATEGORY_MAP.items():
            if key in slug.lower():
                return category
        return ""

    async def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object."""
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                return BeautifulSoup(response.text, "html.parser")
        except Exception:
            pass
        return None

    async def scrape_category(
        self, category: str, max_items: int = 50
    ) -> list[MauiProduct]:
        """Scrape products from a category page.

        category: internal slug like "hombre-poleras" or "mujer-chaquetas"
        """
        path = self.CATEGORY_PATHS.get(category, f"/{category}.html")
        url = f"{self.BASE_URL}{path}"

        soup = await self.get_page(url)
        if not soup:
            return []

        gender = self._infer_gender(path)
        frontend_category = self._map_category(category)
        display_category = f"{frontend_category} {gender}".strip() if frontend_category else category

        # Magento 2 product list selectors
        items = (
            soup.select(".product-item-info")
            or soup.select(".product-item")
            or soup.select(".product.product-item")
        )

        products = []
        for item in items[:max_items]:
            try:
                product = self._parse_product(item, display_category)
                if product:
                    products.append(product)
            except Exception:
                continue

        return products

    async def search_products(
        self, query: str, max_items: int = 30
    ) -> list[MauiProduct]:
        """Search products by keyword using Magento 2 search."""
        url = f"{self.BASE_URL}/catalogsearch/result/"
        products = []

        try:
            response = await self.client.get(
                url,
                params={"q": query},
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            items = (
                soup.select(".product-item-info")
                or soup.select(".product-item")
            )

            for item in items[:max_items]:
                try:
                    product = self._parse_product(item, query)
                    if product:
                        products.append(product)
                except Exception:
                    continue
        except Exception:
            pass

        return products

    def _parse_product(self, item: BeautifulSoup, category: str) -> Optional[MauiProduct]:
        """Parse a Magento 2 product item."""
        # Product name
        name = ""
        name_elem = (
            item.select_one(".product-item-link")
            or item.select_one(".product-name a")
            or item.select_one("[itemprop='name']")
            or item.select_one("a.product-item-link")
        )
        if name_elem:
            name = name_elem.get_text(strip=True)

        if not name:
            return None

        # Price (Magento 2 price box)
        price = 0.0
        price_elem = (
            item.select_one(".price-box .special-price .price")
            or item.select_one(".price-box .price")
            or item.select_one("[data-price-amount]")
            or item.select_one(".price")
        )
        if price_elem:
            # Try data attribute first
            price_amount = price_elem.get("data-price-amount")
            if price_amount:
                try:
                    price = float(price_amount)
                except ValueError:
                    pass
            else:
                price_text = price_elem.get_text(strip=True)
                price = self._normalize_price(price_text)

        # Product ID
        product_id = ""
        id_elem = (
            item.select_one("[data-product-id]")
            or item.select_one("[data-product-sku]")
            or item.select_one("[data-product-code]")
        )
        if id_elem:
            product_id = (
                id_elem.get("data-product-id")
                or id_elem.get("data-product-sku")
                or id_elem.get("data-product-code", "")
            )

        if not product_id:
            # Extract from product URL
            link = item.select_one("a[href]")
            if link:
                href = link.get("href", "")
                match = re.search(r"/([^/]+)\.html$", href)
                if match:
                    product_id = match.group(1)

        if not product_id:
            product_id = re.sub(r"[^a-z0-9]", "-", name.lower())[:50]

        # Image
        image_url = ""
        img_elem = (
            item.select_one(".product-image-photo")
            or item.select_one(".product-image img")
            or item.select_one("img.product-image-photo")
            or item.select_one("img[src*='media']")
        )
        if img_elem:
            image_url = img_elem.get("src", "")
            if not image_url:
                image_url = img_elem.get("data-src", "")
            # Clean up Magento image URL
            if image_url and "?" in image_url:
                image_url = image_url.split("?")[0]

        # Product URL
        original_url = ""
        link_elem = item.select_one("a.product-item-link") or item.select_one("a[href]")
        if link_elem:
            href = link_elem.get("href", "")
            if href.startswith("http"):
                original_url = href
            elif href.startswith("/"):
                original_url = f"{self.BASE_URL}{href}"

        # Sizes (from swatch or size list)
        sizes = []
        size_elems = item.select(".swatch-option.text[data-option-label], .size-option, .size-list li")
        for s in size_elems:
            label = s.get("data-option-label", "") or s.get_text(strip=True)
            if label and label not in sizes:
                sizes.append(label)

        # Colors (from swatch)
        colors = []
        color_elems = item.select(".swatch-option.color[data-option-label], .color-option")
        for c in color_elems:
            label = c.get("data-option-label", "") or c.get_text(strip=True)
            if label and label not in colors:
                colors.append(label)

        # Availability
        availability = True
        stock_elem = item.select_one(".stock, .availability, .out-of-stock")
        if stock_elem:
            stock_text = stock_elem.get_text(strip=True).lower()
            if "out" in stock_text or "agotado" in stock_text or "sin stock" in stock_text:
                availability = False

        return MauiProduct(
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
        """Normalize Chilean price string to float."""
        # Handle formats: "$14.990", "14990", "$14.990 CLP"
        cleaned = re.sub(r"[^\d.,]", "", price_str)
        # Chile uses . as thousands separator and , as decimal
        if "." in cleaned and "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "." in cleaned:
            # Could be thousands separator or decimal
            parts = cleaned.split(".")
            if len(parts) > 2:
                # Multiple dots = thousands separator
                cleaned = cleaned.replace(".", "")
            elif len(parts[-1]) == 3:
                # Likely thousands separator (e.g., "14.990")
                cleaned = cleaned.replace(".", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
