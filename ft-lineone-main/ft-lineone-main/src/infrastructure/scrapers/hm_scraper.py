from typing import List, Dict, Any
from bs4 import BeautifulSoup
from src.infrastructure.scrapers.base_scraper import BaseScraper


class HMScraper(BaseScraper):
    def __init__(self):
        super().__init__("hm", "https://www2.hm.com")

    async def scrape_category(self, category: str, max_items: int) -> List[Dict[str, Any]]:
        category_urls = {
            "woman_tshirts": "/es_es/mujer/comprar-por-producto/camisetas.html",
            "woman_dresses": "/es_es/mujer/comprar-por-producto/vestidos.html",
            "woman_pants": "/es_es/mujer/comprar-por-producto/pantalones.html",
            "woman_jackets": "/es_es/mujer/comprar-por-producto/chaquetas.html",
            "man_tshirts": "/es_es/hombre/comprar-por-producto/camisetas.html",
            "man_shirts": "/es_es/hombre/comprar-por-producto/camisas.html",
            "man_pants": "/es_es/hombre/comprar-por-producto/pantalones.html",
            "man_jackets": "/es_es/hombre/comprar-por-producto/chaquetas.html",
        }

        url_path = category_urls.get(category, "/es_es/mujer/comprar-por-producto/camisetas.html")
        url = f"{self.base_url}{url_path}"

        soup = await self._fetch_page(url)
        products = []

        product_cards = soup.select("article.item")[:max_items]
        for card in product_cards:
            try:
                link_elem = card.select_one("a.item-link")
                product_url = link_elem["href"] if link_elem else ""
                if product_url and not product_url.startswith("http"):
                    product_url = f"https://www2.hm.com{product_url}"

                name_elem = card.select_one("h3.item-heading a")
                name = name_elem.get_text(strip=True) if name_elem else ""

                price_elem = card.select_one("span.price")
                price_text = price_elem.get_text(strip=True) if price_elem else "0"
                price = self._parse_price(price_text)

                img_elem = card.select_one("img.item-image")
                image_url = img_elem.get("data-src") or img_elem.get("src") or ""

                external_id = ""
                if product_url:
                    import re
                    match = re.search(r"/(\d+)\.html", product_url)
                    if match:
                        external_id = match.group(1)

                if external_id and name and price > 0:
                    products.append({
                        "external_id": external_id,
                        "name": name,
                        "price": price,
                        "currency": "EUR",
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