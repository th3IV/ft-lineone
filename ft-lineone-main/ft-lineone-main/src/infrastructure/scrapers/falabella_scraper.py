from typing import List, Dict, Any
from bs4 import BeautifulSoup
from src.infrastructure.scrapers.base_scraper import BaseScraper


class FalabellaScraper(BaseScraper):
    def __init__(self):
        super().__init__("falabella", "https://www.falabella.com")

    async def scrape_category(self, category: str, max_items: int) -> List[Dict[str, Any]]:
        category_urls = {
            "woman_tshirts": "/falabella-cl/category/cat720001/Mujer-Poleras-y-Poleras",
            "woman_dresses": "/falabella-cl/category/cat720004/Mujer-Vestidos",
            "woman_pants": "/falabella-cl/category/cat720002/Mujer-Pantalones",
            "woman_jackets": "/falabella-cl/category/cat720008/Mujer-Chaquetas-y-Camperas",
            "man_tshirts": "/falabella-cl/category/cat720010/Hombre-Poleras-y-Poleras",
            "man_shirts": "/falabella-cl/category/cat720011/Hombre-Camisas",
            "man_pants": "/falabella-cl/category/cat720012/Hombre-Pantalones",
            "man_jackets": "/falabella-cl/category/cat720017/Hombre-Chaquetas-y-Camperas",
        }

        url_path = category_urls.get(category)
        if not url_path:
            return []
        url = f"{self.base_url}{url_path}"

        soup = await self._fetch_page(url)
        products = []

        product_cards = soup.select("[data-pod], .pod-item, .js-product")[:max_items]
        for card in product_cards:
            try:
                html = str(card)
                product_soup = BeautifulSoup(html, "lxml")

                name = ""
                name_elem = product_soup.select_one("[data-product-name]")
                if name_elem:
                    name = name_elem.get("data-product-name", "")

                price = 0.0
                price_elem = product_soup.select_one(".prices-0 span, [data-price]")
                if price_elem:
                    price_text = price_elem.get("data-price", price_elem.get_text(strip=True))
                    price = self._parse_price(str(price_text))

                product_id = ""
                id_elem = product_soup.select_one("[data-product-id]")
                if id_elem:
                    product_id = id_elem.get("data-product-id", "")

                image_url = ""
                img = product_soup.select_one("img[data-src], img")
                if img:
                    image_url = img.get("data-src") or img.get("src") or ""

                if product_id and name and price > 0:
                    products.append({
                        "external_id": f"fal-{product_id}",
                        "name": name,
                        "price": price,
                        "currency": "CLP",
                        "image_url": image_url,
                        "category": category,
                        "product_url": f"{self.base_url}/falabella-cl/product/{product_id}",
                    })
            except Exception:
                continue

        return products

    def _parse_price(self, price_text: str) -> float:
        import re
        cleaned = re.sub(r"[^\d.,]", "", price_text)
        cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
