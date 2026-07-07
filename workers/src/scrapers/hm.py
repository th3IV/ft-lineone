"""H&M Chile scraper — VTEX catalog_system products search API.

H&M Chile (cl.hm.com) runs on VTEX. The catalog_system API returns proper
search results (not the limited intelligent-search endpoint).

Endpoint:
  GET /api/catalog_system/pub/products/search/?q={query}&_from=0&_to=29
"""

import json
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class HMProduct:
    """H&M product data."""
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


class HMScraper:
    """Scraper for H&M Chile (cl.hm.com) using VTEX catalog_system API."""

    BASE_URL = "https://cl.hm.com"
    SEARCH_URL = "https://cl.hm.com/api/catalog_system/pub/products/search/?q={query}&_from=0&_to={to}"

    CATEGORY_KEYWORDS = {
        "POLERA": "Poleras",
        "POLERAS": "Poleras",
        "TOPS": "Poleras",
        "REMERA": "Poleras",
        "CAMISETA": "Poleras",
        "T-SHIRT": "Poleras",
        "CAMISA": "Camisas",
        "BLUSA": "Camisas",
        "SHIRT": "Camisas",
        "PANTALON": "Pantalones",
        "PANTALONES": "Pantalones",
        "JEAN": "Pantalones",
        "JEANS": "Pantalones",
        "BERMUDA": "Shorts",
        "SHORT": "Shorts",
        "CHAQUETA": "Chaquetas",
        "ABRIGO": "Chaquetas",
        "PARKA": "Chaquetas",
        "BLAZER": "Chaquetas",
        "VESTIDO": "Vestidos",
        "DRESS": "Vestidos",
        "FALDA": "Faldas",
        "SKIRT": "Faldas",
        "POLERON": "Polerones",
        "POLERONES": "Polerones",
        "BUZO": "Polerones",
        "SUDADERA": "Polerones",
        "SWEATSHIRT": "Polerones",
        "HOODIE": "Polerones",
    }

    def __init__(self):
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                timeout=30.0,
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
        """Infer frontend category from category path text."""
        t = text.upper()
        for keyword, category in self.CATEGORY_KEYWORDS.items():
            if keyword in t:
                return category
        return ""

    async def search_products(self, query: str, max_items: int = 30) -> list[HMProduct]:
        """Search products via H&M VTEX catalog_system API."""
        client = await self._get_client()
        to = max_items - 1 if max_items > 0 else 29
        url = self.SEARCH_URL.format(query=query, to=to)
        products = []

        try:
            resp = await client.get(url)
            if resp.status_code not in (200, 206):
                print(json.dumps({"event": "hm_search_error", "query": query, "status": resp.status_code}))
                return []
            data = resp.json()
            if not isinstance(data, list):
                print(json.dumps({"event": "hm_search_error", "query": query, "error": "non-list response", "type": str(type(data))}))
                return []
            for item in data[:max_items]:
                product = self._parse_product(item, query)
                if product and product.name:
                    products.append(product)
        except Exception as e:
            print(json.dumps({"event": "hm_search_error", "query": query, "error": str(e)}))

        return products[:max_items]

    async def scrape_category(self, category: str, max_items: int = 50) -> list[HMProduct]:
        """Scrape products from a category using search."""
        return await self.search_products(category, max_items)

    def _parse_product(self, item: dict, query: str) -> Optional[HMProduct]:
        """Parse a product from VTEX catalog_system response."""
        if not isinstance(item, dict):
            return None

        product_id = str(item.get("productId", "") or item.get("productReference", ""))
        if not product_id:
            return None

        name = item.get("productName", "")
        if not name:
            return None

        # Price from items[0].sellers[0].commertialOffer.Price
        price = 0.0
        items_list = item.get("items", [])
        if items_list and isinstance(items_list, list):
            first_item = items_list[0]
            sellers = first_item.get("sellers", [])
            if sellers and isinstance(sellers, list):
                offer = sellers[0].get("commertialOffer", {})
                offer_price = offer.get("Price", 0) or offer.get("ListPrice", 0) or offer.get("spotPrice", 0)
                try:
                    price = float(offer_price)
                except (ValueError, TypeError):
                    pass

        # Image + all images + colors from items
        image_url = ""
        image_urls = []
        colors = []
        if items_list and isinstance(items_list, list):
            for item_obj in items_list:
                if not isinstance(item_obj, dict):
                    continue
                images = item_obj.get("images", [])
                if images and isinstance(images, list):
                    for img in images:
                        if isinstance(img, dict):
                            img_url = img.get("imageUrl", "")
                            if img_url and img_url not in image_urls:
                                image_urls.append(img_url)

                # Color from complementName (e.g., "Beige", "Negro")
                color_name = item_obj.get("complementName", "")
                if color_name and color_name not in colors:
                    colors.append(color_name)

            if image_urls:
                image_url = image_urls[0]

        # URL — full URL already provided
        original_url = item.get("link", "") or f"{self.BASE_URL}/{product_id}/p"

        # Category + Gender from categories path array
        category = ""
        gender = ""
        categories = item.get("categories", [])
        if categories and isinstance(categories, list):
            path_text = " ".join(str(c).upper() for c in categories)
            if "HOMBRE" in path_text or "MEN" in path_text:
                gender = "hombre"
            elif "MUJER" in path_text or "WOMEN" in path_text or "LADIES" in path_text:
                gender = "mujer"
            for cat in categories:
                cat_str = str(cat).upper()
                mapped = self._infer_category(cat_str)
                if mapped:
                    category = mapped
                    break

        if not category:
            category = self._infer_category(name) or self._infer_category(query)

        if not gender:
            q = query.lower()
            if "hombre" in q or "men" in q:
                gender = "hombre"
            elif "mujer" in q or "women" in q:
                gender = "mujer"

        display_category = f"{category} {gender}".strip() if category else query

        # Sizes from items[].nameComplete
        sizes = []
        if items_list and isinstance(items_list, list):
            for item_obj in items_list:
                if not isinstance(item_obj, dict):
                    continue
                size_name = item_obj.get("nameComplete", "") or item_obj.get("name", "")
                sellers = item_obj.get("sellers", [])
                if sellers and isinstance(sellers, list):
                    offer = sellers[0].get("commertialOffer", {})
                    avail = offer.get("AvailableQuantity", 0)
                    if avail > 0 and size_name:
                        # Try " - " separator first (VTEX classic format)
                        parts = size_name.split(" - ")
                        if len(parts) > 1:
                            size_val = parts[-1].strip()
                        else:
                            # Fallback: extract size from name vs productName
                            # name is usually "ProductName Size" (e.g. "Trenchcoat XXS")
                            size_val = size_name.replace(name, "").strip()
                        if size_val and size_val not in sizes:
                            sizes.append(size_val)

        # Availability
        availability = True
        if items_list and isinstance(items_list, list):
            first_item = items_list[0]
            sellers = first_item.get("sellers", [])
            if sellers and isinstance(sellers, list):
                offer = sellers[0].get("commertialOffer", {})
                if offer.get("AvailableQuantity", 0) == 0:
                    availability = False

        return HMProduct(
            external_id=product_id,
            name=name,
            price=price,
            currency="CLP",
            image_url=image_url,
            category=display_category,
            sizes=sizes,
            colors=colors,
            description=item.get("description", "") or item.get("metaTagDescription", ""),
            availability=availability,
            original_url=original_url,
            image_urls=image_urls,
        )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
