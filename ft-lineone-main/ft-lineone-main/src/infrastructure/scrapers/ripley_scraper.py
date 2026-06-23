from typing import List, Dict, Any
from bs4 import BeautifulSoup
from src.infrastructure.scrapers.base_scraper import BaseScraper


class RipleyScraper(BaseScraper):
    def __init__(self):
        super().__init__("ripley", "https://www.ripley.com")

    async def scrape_category(self, category: str, max_items: int) -> List[Dict[str, Any]]:
        category_urls = {
            "woman_tshirts": "/mujer/ropa/poleras",
            "woman_dresses": "/mujer/ropa/vestidos",
            "woman_pants": "/mujer/ropa/pantalones",
            "woman_jackets": "/mujer/ropa/chaquetas",
            "man_tshirts": "/hombre/ropa/poleras",
            "man_shirts": "/hombre/ropa/camisas",
            "man_pants": "/hombre/ropa/pantalones",
            "man_jackets": "/hombre/ropa/chaquetas",
        }

        url_path = category_urls.get(category)
        if not url_path:
            return []
        url = f"{self.base_url}{url_path}"

        soup = await self._fetch_page(url)
        products = []

        product_cards = soup.select(".catalog-product-item, article.product-item, .product-card")[:max_items]
        for card in product_cards:
            try:
                link = card.select_one("a.product-link, a[href*='/product/']")
                product_url = ""
                if link:
                    href = link.get("href", "")
                    product_url = href if href.startswith("http") else f"https://www.ripley.com{href}"

                name_elem = card.select_one(".product-name, h2, h3, [data-name]")
                name = name_elem.get_text(strip=True) if name_elem else ""

                price_elem = card.select_one(".product-price, .price, [data-price]")
                price = 0.0
                if price_elem:
                    price_text = price_elem.get("data-price", price_elem.get_text(strip=True))
                    price = self._parse_price(str(price_text))

                img = card.select_one("img[data-src], img")
                image_url = ""
                if img:
                    image_url = img.get("data-src") or img.get("src") or ""

                import re
                ext_id = ""
                if product_url:
                    match = re.search(r"/product/(\d+)", product_url)
                    if match:
                        ext_id = match.group(1)

                if ext_id and name and price > 0:
                    products.append({
                        "external_id": f"rip-{ext_id}",
                        "name": name,
                        "price": price,
                        "currency": "CLP",
                        "image_url": image_url,
                        "category": category,
                        "product_url": product_url,
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
