from typing import List

import requests
from bs4 import BeautifulSoup

from scrapers.collectors.base_scraper import BaseScraper
from scrapers.models.product_dto import ProductDTO


class FalabellaScraper(BaseScraper):

    def __init__(self):
        super().__init__("falabella", "https://www.falabella.com")

    def scrape(self, category: str, max_items: int) -> List[ProductDTO]:
        products = []
        url = f"{self.base_url}/falabella-cl/category/{category}"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            items = soup.select("[data-pod]") or soup.select(".pod-item") or soup.select(".js-product")
            for item in items[:max_items]:
                try:
                    html = str(item)
                    product = self.parse_product(html, category)
                    products.append(product)
                except Exception:
                    continue
        except requests.RequestException:
            products = self._generate_mock_data(category, max_items)

        return products

    def parse_product(self, html: str, category: str = "") -> ProductDTO:
        soup = BeautifulSoup(html, "lxml")

        try:
            name = soup.select_one("[data-product-name]")["data-product-name"]
        except (AttributeError, KeyError, TypeError):
            name = ""

        try:
            price = self.normalize_price(
                soup.select_one(".prices-0 span")["data-price"]
            )
        except (AttributeError, KeyError, TypeError):
            try:
                price = float(soup.select_one(".price")["data-price"])
            except (AttributeError, KeyError, TypeError):
                price = 0.0

        try:
            product_id = soup.select_one("[data-product-id]")["data-product-id"]
        except (AttributeError, KeyError, TypeError):
            product_id = ""

        try:
            image = soup.select_one("img[data-src]")["data-src"]
        except (AttributeError, KeyError, TypeError):
            try:
                image = soup.select_one("img")["src"]
            except (AttributeError, KeyError, TypeError):
                image = ""

        try:
            description = soup.select_one("[data-description]").get_text(strip=True)
        except AttributeError:
            description = ""

        try:
            sizes = [
                s.get_text(strip=True)
                for s in soup.select("[data-size]")
            ]
        except Exception:
            sizes = []

        try:
            colors = [
                c.get_text(strip=True)
                for c in soup.select("[data-color]")
            ]
        except Exception:
            colors = []

        try:
            availability = "out-of-stock" not in (
                soup.select_one("[data-stock]").get("class", [])
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

    def _generate_mock_data(self, category: str, max_items: int) -> List[ProductDTO]:
        mock_products = [
            {
                "external_id": "FAL-001",
                "name": "Zapatillas Deportivas Falabella",
                "description": "Zapatillas running confort",
                "price": 39990.0,
                "image": "https://falabella.com/img/shoe1.jpg",
            },
            {
                "external_id": "FAL-002",
                "name": "Chaqueta Impermeable Hombre",
                "description": "Chaqueta cortavientos",
                "price": 59990.0,
                "image": "https://falabella.com/img/jacket1.jpg",
            },
            {
                "external_id": "FAL-003",
                "name": "Jeans Slim Fit Mujer",
                "description": "Jeans elastizados",
                "price": 24990.0,
                "image": "https://falabella.com/img/jeans1.jpg",
            },
            {
                "external_id": "FAL-004",
                "name": "Polera Algodón Premium",
                "description": "Polera cuello redondo",
                "price": 14990.0,
                "image": "https://falabella.com/img/tshirt1.jpg",
            },
            {
                "external_id": "FAL-005",
                "name": "Vestido Estampado Floral",
                "description": "Vestido largo floreado",
                "price": 34990.0,
                "image": "https://falabella.com/img/dress1.jpg",
            },
        ]
        return [
            ProductDTO(
                external_id=p["external_id"],
                store=self.store_name,
                name=p["name"],
                description=p["description"],
                price=p["price"],
                currency="CLP",
                original_url=f"{self.base_url}/product/{p['external_id']}",
                image_urls=[p["image"]],
                category=category,
                sizes=["S", "M", "L", "XL"],
                colors=["Negro", "Blanco", "Azul"],
                availability=True,
            )
            for p in mock_products[:max_items]
        ]
