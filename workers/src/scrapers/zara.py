"""Zara scraper - Internal API extraction (Chile locale).

Uses Zara's internal category + product API:
  GET /cl/es/categories?ajax=true          → category tree
  GET /cl/es/category/{id}/products?ajax=true → products per leaf category
"""

import json
import httpx
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ZaraProduct:
    """Zara product data."""
    external_id: str
    name: str
    price: float
    currency: str
    image_url: str
    category: str
    sizes: list[str] = field(default_factory=list)
    colors: list[str] = field(default_factory=list)
    description: str = ""
    availability: bool = True
    original_url: str = ""


# Top-level Zara Chile category IDs (from /cl/es/categories?ajax=true)
SECTION_IDS = {
    "mujer": 1009502,
    "hombre": 1009547,
}

# Leaf subcategories we want to scrape (clothing only, no accessories)
LEAF_CATEGORIES = {
    "mujer": [
        2509383,   # VESTIDOS | MONOS
        2509382,   # VESTIDOS
        2509505,   # CAMISETAS MANGA CORTA
        2509497,   # CAMISETAS MANGA LARGA
        2510965,   # CAMISETAS
        2509523,   # PANTALONES
        2509574,   # JEANS
        2509558,   # FALDAS
        2509611,   # ABRIGOS Y MONOS
        2509608,   # ABRIGOS
        2509548,   # FUNDAS
        2509635,   # SUDADERAS
        2509623,   # BUZOS
    ],
    "hombre": [
        2510635,   # CAMISETAS
        2510640,   # POLOS
        2510650,   # PANTALONES
        2510657,   # JEANS
        2510670,   # ABRIGOS
        2510664,   # SUDADERAS
        2510673,   # BUZOS
        2510695,   # CHAQUETAS
    ],
}


class ZaraScraper:
    """Scraper for Zara (zara.com/cl/es) using internal JSON API."""

    BASE_URL = "https://www.zara.com/cl/es"
    CATEGORIES_URL = "https://www.zara.com/cl/es/categories?ajax=true"
    PRODUCTS_URL = "https://www.zara.com/cl/es/category/{cat_id}/products?ajax=true"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://www.zara.com/cl/es/",
            },
        )

    async def get_category_tree(self) -> list[dict]:
        """Fetch full category tree from Zara API."""
        try:
            resp = await self.client.get(self.CATEGORIES_URL)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []

    async def get_products_for_category(self, cat_id: int) -> list[dict]:
        """Fetch products for a specific category ID."""
        url = self.PRODUCTS_URL.format(cat_id=cat_id)
        try:
            resp = await self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("productGroups", [])
        except Exception:
            pass
        return []

    def _parse_products_from_groups(self, product_groups: list[dict], category: str) -> list[ZaraProduct]:
        """Extract ZaraProduct objects from productGroups response."""
        products = []
        seen_ids = set()

        for group in product_groups:
            elements = group.get("elements", [])
            for element in elements:
                # commercialComponents contains the actual product data
                components = element.get("commercialComponents", [])
                for comp in components:
                    product = self._parse_component(comp, category)
                    if product and product.external_id not in seen_ids:
                        seen_ids.add(product.external_id)
                        products.append(product)

        return products

    def _parse_component(self, comp: dict, category: str) -> Optional[ZaraProduct]:
        """Parse a single commercialComponent into a ZaraProduct."""
        try:
            # Skip non-product types (bundles, marketing, etc.)
            kind = comp.get("kind", "")
            if kind in ("Bundle", "Marketing", "Editorial"):
                return None

            name = comp.get("name", "")
            if not name:
                return None

            # ID
            product_id = str(comp.get("id", ""))
            reference = comp.get("reference", "")

            # Price (in CLP, minor units — divide by 100)
            price_raw = comp.get("price", 0)
            if isinstance(price_raw, dict):
                # Try discountedPrice first, then regular price
                price = float(
                    price_raw.get("discountedAmount", 0)
                    or price_raw.get("value", 0)
                    or price_raw.get("price", 0)
                    or 0
                )
            elif isinstance(price_raw, (int, float)):
                price = float(price_raw)
            else:
                price = 0.0

            # Price is already in CLP (Chilean pesos), no conversion needed

            # Image URL from detail.colors[].xmedia[]
            image_url = ""
            detail = comp.get("detail", {})
            colors = detail.get("colors", [])
            if colors:
                first_color = colors[0]
                xmedia = first_color.get("xmedia", [])
                if xmedia:
                    media = xmedia[0]
                    url_template = media.get("url", "")
                    if url_template:
                        image_url = url_template.replace("{width}", "800")

            # SEO URL
            seo = comp.get("seo", {})
            keyword = seo.get("keyword", "")
            seo_url = seo.get("seoUrl", "")
            if seo_url:
                original_url = f"https://www.zara.com{seo_url}"
            elif keyword:
                original_url = f"{self.BASE_URL}/{keyword}-p{product_id}.html"
            else:
                original_url = f"{self.BASE_URL}/search?search={name.replace(' ', '+')}"

            # Colors
            color_names = []
            for c in colors:
                cname = c.get("name", "")
                if cname:
                    color_names.append(cname)

            # Availability
            availability = True
            avail_info = comp.get("availability", "")
            if "OutOfStock" in str(avail_info) or avail_info == "out_of_stock":
                availability = False

            return ZaraProduct(
                external_id=product_id or reference,
                name=name,
                price=price,
                currency="CLP",
                image_url=image_url,
                category=category,
                sizes=[],
                colors=color_names,
                description=detail.get("description", ""),
                availability=availability,
                original_url=original_url,
            )
        except Exception:
            return None

    async def scrape_category(self, category: str, max_items: int = 20) -> list[ZaraProduct]:
        """Scrape products for a given top-level category (mujer/hombre).

        Fetches all leaf subcategories and deduplicates products.
        """
        cat_id = SECTION_IDS.get(category)
        if not cat_id:
            return []

        leaf_ids = LEAF_CATEGORIES.get(category, [])
        if not leaf_ids:
            # Fallback: fetch the section itself
            leaf_ids = [cat_id]

        all_products = []
        seen_ids = set()

        for leaf_id in leaf_ids:
            if len(all_products) >= max_items:
                break

            try:
                groups = await self.get_products_for_category(leaf_id)
                products = self._parse_products_from_groups(groups, category)

                for p in products:
                    if p.external_id not in seen_ids and len(all_products) < max_items:
                        seen_ids.add(p.external_id)
                        all_products.append(p)
            except Exception:
                continue

        return all_products[:max_items]

    async def scrape_all(self, max_per_category: int = 20) -> list[ZaraProduct]:
        """Scrape both mujer and hombre categories."""
        all_products = []
        for category in SECTION_IDS:
            products = await self.scrape_category(category, max_per_category)
            all_products.extend(products)
        return all_products

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
