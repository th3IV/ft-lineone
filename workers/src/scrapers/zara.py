"""Zara scraper — Internal API extraction (Chile locale).

Uses Zara's internal category + product API:
  GET /cl/es/category/{id}/products?ajax=true → products per leaf category

The ?ajax=true endpoint returns full product JSON without bot detection
when using the correct internal category IDs (2509xxx range).

Key: Do NOT fetch the HTML pages (Akamai bot detection). Only use ?ajax=true.
"""

import json
import traceback
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
    image_urls: list[str] = field(default_factory=list)


# Internal Zara Chile category IDs (confirmed working via ?ajax=true)
# These are NOT the same as URL slug IDs (l1009, etc.)
LEAF_CATEGORIES = {
    "mujer": [
        2509505,   # CAMISETAS MANGA CORTA (37 products)
        2509498,   # CAMISETAS/POLERAS (146 products)
        2509501,   # TOPS (97 products)
        2509382,   # VESTIDOS
        2509523,   # PANTALONES
        2509574,   # JEANS
        2725920,   # FALDAS|SHORTS
        2510408,   # CAZADORAS|CHAQUETAS
        2510443,   # ABRIGOS|TRENCH
        2509635,   # SUDADERAS
        2509623,   # BUZOS
    ],
    "hombre": [
        2510635,   # CAMISETAS
        2510691,   # POLOS
        2510591,   # PANTALONES
        2510594,   # JEANS
        2510654,   # ABRIGOS
        2510658,   # CAZADORAS|CHAQUETAS
        2510703,   # POLERONES
    ],
}

# Map Zara familyName to frontend categories
CATEGORY_MAP = {
    "VESTIDOS": "Vestidos",
    "VESTIDOS | MONOS": "Vestidos",
    "MONOS": "Vestidos",
    "CAMISETAS": "Poleras",
    "CAMISETAS MANGA CORTA": "Poleras",
    "CAMISETAS MANGA LARGA": "Poleras",
    "POLOS": "Poleras",
    "PANTALONES": "Pantalones",
    "JEANS": "Pantalones",
    "FALDAS": "Faldas",
    "SHORTS": "Shorts",
    "CHAQUETAS": "Chaquetas",
    "CAZADORAS": "Chaquetas",
    "ABRIGOS": "Chaquetas",
    "ABRIGOS | TRENCH": "Chaquetas",
    "TRENCH": "Chaquetas",
    "SUDADERAS": "Polerones",
    "BUZOS": "Polerones",
    "POLERONES": "Polerones",
}


class ZaraScraper:
    """Scraper for Zara (zara.com/cl/es) using internal JSON API."""

    BASE_URL = "https://www.zara.com/cl/es"
    PRODUCTS_URL = "https://www.zara.com/cl/es/category/{cat_id}/products?ajax=true"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
            },
        )

    async def get_products_for_category(self, cat_id: int) -> list[dict]:
        """Fetch products for a specific internal category ID via ?ajax=true."""
        url = self.PRODUCTS_URL.format(cat_id=cat_id)
        try:
            resp = await self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("productGroups", [])
            print(f"[zara] Category {cat_id} returned status {resp.status_code}")
        except Exception as e:
            print(f"[zara] Error fetching category {cat_id}: {type(e).__name__}: {e}")
        return []

    def _parse_products_from_groups(self, product_groups: list[dict], gender: str) -> list[ZaraProduct]:
        """Extract ZaraProduct objects from productGroups response."""
        products = []
        seen_ids = set()

        for group in product_groups:
            elements = group.get("elements", [])
            for element in elements:
                components = element.get("commercialComponents", [])
                for comp in components:
                    product = self._parse_component(comp, gender)
                    if product and product.external_id not in seen_ids:
                        seen_ids.add(product.external_id)
                        products.append(product)

        return products

    def _parse_component(self, comp: dict, gender: str) -> Optional[ZaraProduct]:
        """Parse a single commercialComponent into a ZaraProduct."""
        try:
            kind = comp.get("kind", "")
            if kind in ("Bundle", "Marketing", "Editorial"):
                return None

            name = comp.get("name", "")
            if not name:
                return None

            product_id = str(comp.get("id", ""))

            # Price (in CLP)
            price_raw = comp.get("price", 0)
            if isinstance(price_raw, dict):
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

            # Image URLs from detail.colors[].xmedia[]
            image_url = ""
            image_urls = []
            detail = comp.get("detail", {})
            colors_data = detail.get("colors", [])
            if colors_data:
                for color in colors_data:
                    xmedia = color.get("xmedia", [])
                    for media in xmedia:
                        url_template = media.get("url", "")
                        if url_template:
                            full_url = url_template.replace("{width}", "800")
                            if full_url not in image_urls:
                                image_urls.append(full_url)
                if image_urls:
                    image_url = image_urls[0]

            # SEO URL
            seo = comp.get("seo", {})
            keyword = seo.get("keyword", "")
            seo_product_id = seo.get("seoProductId", "")
            seo_url = seo.get("seoUrl", "")

            if seo_url and seo_product_id:
                original_url = f"https://www.zara.com{seo_url}"
            elif keyword and seo_product_id:
                original_url = f"{self.BASE_URL}/{keyword}-p{seo_product_id}.html"
            elif product_id:
                original_url = f"{self.BASE_URL}/search?search={name.replace(' ', '+')}"
            else:
                original_url = ""

            # Sizes
            sizes = []
            for s in detail.get("sizes", []):
                size_name = s.get("name", "")
                if size_name:
                    sizes.append(size_name)

            # Colors
            color_names = []
            for c in colors_data:
                cname = c.get("name", "")
                if cname:
                    color_names.append(cname)

            # Category from familyName
            family_name = comp.get("familyName", "")
            category = CATEGORY_MAP.get(family_name, family_name)
            if not category:
                category = gender
            # Include gender in category for filtering
            if gender:
                category = f"{category} {gender}".strip()

            # Availability
            availability = True
            avail_info = comp.get("availability", "")
            if "OutOfStock" in str(avail_info) or avail_info == "out_of_stock":
                availability = False

            return ZaraProduct(
                external_id=product_id,
                name=name,
                price=price,
                currency="CLP",
                image_url=image_url,
                category=category,
                sizes=sizes,
                colors=color_names,
                description=detail.get("description", ""),
                availability=availability,
                original_url=original_url,
                image_urls=image_urls,
            )
        except Exception as e:
            print(json.dumps({
                "event": "zara_parse_error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "component_id": comp.get("id") if isinstance(comp, dict) else None,
                "component_name": comp.get("name") if isinstance(comp, dict) else None,
            }))
            return None

    async def scrape_category(self, category: str, max_items: int = 20) -> list[ZaraProduct]:
        """Scrape products for a given top-level category (mujer/hombre).

        Fetches all leaf subcategories and deduplicates products.
        """
        leaf_ids = LEAF_CATEGORIES.get(category, [])
        if not leaf_ids:
            return []

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

    async def search_products(self, query: str, max_items: int = 30) -> list[ZaraProduct]:
        """Search is not directly supported by the ?ajax=true endpoint.

        Fallback: scrape mujer + hombre categories and filter by query keywords.
        """
        all_products = await self.scrape_category("mujer", max_items)
        all_products.extend(await self.scrape_category("hombre", max_items))

        # Filter by query keywords
        q = query.lower()
        filtered = []
        for p in all_products:
            if q in p.name.lower():
                filtered.append(p)

        return filtered[:max_items] if filtered else all_products[:max_items]

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
