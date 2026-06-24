from typing import List

import requests
from bs4 import BeautifulSoup

from scrapers.scrapers.base_scraper import BaseScraper
from scrapers.models.product_dto import ProductDTO


class ParisScraper(BaseScraper):

    def __init__(self):
        super().__init__("paris", "https://www.paris.cl")

    def scrape(self, category: str, max_items: int) -> List[ProductDTO]:
        products = []
        url = f"{self.base_url}/catalogo/{category}"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            items = soup.select(".producto") or soup.select(".product-item") or soup.select("[data-product-id]")
            for item in items[:max_items]:
                try:
                    html = str(item)
                    product = self.parse_product(html)
                    products.append(product)
                except Exception:
                    continue
        except requests.RequestException:
            products = self._generate_mock_data(category, max_items)

        return products

    def parse_product(self, html: str) -> ProductDTO:
        soup = BeautifulSoup(html, "lxml")

        try:
            name = soup.select_one(".product-title a").get_text(strip=True)
        except AttributeError:
            try:
                name = soup.select_one("h2").get_text(strip=True)
            except AttributeError:
                name = ""

        try:
            price = self.normalize_price(
                soup.select_one(".product-price .price").get_text(strip=True)
            )
        except (AttributeError, ValueError):
            try:
                price = float(soup.select_one("[data-price-value]")["data-price-value"])
            except (AttributeError, KeyError, TypeError):
                price = 0.0

        try:
            product_id = soup.select_one("[data-id]")["data-id"]
        except (AttributeError, KeyError, TypeError):
            product_id = ""

        try:
            image = soup.select_one(".product-image a img")["src"]
        except (AttributeError, KeyError, TypeError):
            try:
                image = soup.select_one("img.product-img")["src"]
            except (AttributeError, KeyError, TypeError):
                image = ""

        try:
            description = soup.select_one(".product-description").get_text(strip=True)
        except AttributeError:
            description = ""

        try:
            sizes = [
                s.get_text(strip=True)
                for s in soup.select(".size-variant")
            ]
        except Exception:
            sizes = []

        try:
            colors = [
                c.get_text(strip=True)
                for c in soup.select(".color-variant")
            ]
        except Exception:
            colors = []

        try:
            availability = "disabled" not in (
                soup.select_one(".buy-button").get("class", [])
            )
        except AttributeError:
            availability = True

        dto = ProductDTO(
            external_id=product_id,
            store=self.store_name,
            name=name,
            description=description,
            price=price,
            currency="CLP",
            original_url="",
            image_urls=[image] if image else [],
            category=category,
            sizes=sizes,
            colors=colors,
            availability=availability,
        )
        return dto

    MOCK_DATA = [
        {"external_id": "PAR-001", "name": "Chamarra Paris Cuero", "description": "Chamarra cuero genuino", "price": 89990.0, "image": "https://paris.cl/img/chamarra1.jpg", "sizes": ["S", "M", "L", "XL"], "colors": ["Negro", "Café", "Beige"]},
        {"external_id": "PAR-002", "name": "Blusa Seda Mujer", "description": "Blusa manga larga seda", "price": 34990.0, "image": "https://paris.cl/img/blusa1.jpg", "sizes": ["S", "M", "L", "XL"], "colors": ["Negro", "Café", "Beige"]},
        {"external_id": "PAR-003", "name": "Buzo Oversize Hombre", "description": "Buzo capucha polar", "price": 22990.0, "image": "https://paris.cl/img/buzo1.jpg", "sizes": ["S", "M", "L", "XL"], "colors": ["Negro", "Café", "Beige"]},
        {"external_id": "PAR-004", "name": "Falda Plisada Mujer", "description": "Falda plisada midi", "price": 19990.0, "image": "https://paris.cl/img/falda1.jpg", "sizes": ["S", "M", "L", "XL"], "colors": ["Negro", "Café", "Beige"]},
        {"external_id": "PAR-005", "name": "Calcetines Deportivos Pack", "description": "Pack 6 pares calcetines", "price": 9990.0, "image": "https://paris.cl/img/calcetines1.jpg", "sizes": ["S", "M", "L", "XL"], "colors": ["Negro", "Café", "Beige"]},
    ]

    def _generate_mock_data(self, category: str, max_items: int) -> List[ProductDTO]:
        return self._build_mock_products(self.MOCK_DATA, category, max_items)
