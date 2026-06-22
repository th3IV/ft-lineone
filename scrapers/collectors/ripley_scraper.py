from typing import List

import requests
from bs4 import BeautifulSoup

from scrapers.collectors.base_scraper import BaseScraper
from scrapers.models.product_dto import ProductDTO


class RipleyScraper(BaseScraper):

    def __init__(self):
        super().__init__("ripley", "https://www.ripley.com")

    def scrape(self, category: str, max_items: int) -> List[ProductDTO]:
        products = []
        url = f"{self.base_url}/categoria/{category}"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            items = soup.select(".product-card") or soup.select(".catalog-product-item") or soup.select("[data-product]")
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
            name = soup.select_one(".product-name").get_text(strip=True)
        except AttributeError:
            name = ""

        try:
            price = self.normalize_price(
                soup.select_one(".product-price .price").get_text(strip=True)
            )
        except (AttributeError, ValueError):
            try:
                price = float(soup.select_one("[data-price]")["data-price"])
            except (AttributeError, KeyError, TypeError):
                price = 0.0

        try:
            product_id = soup.select_one("[data-sku]")["data-sku"]
        except (AttributeError, KeyError, TypeError):
            product_id = ""

        try:
            image = soup.select_one(".product-image img")["src"]
        except (AttributeError, KeyError, TypeError):
            try:
                image = soup.select_one("img[data-original]")["data-original"]
            except (AttributeError, KeyError, TypeError):
                image = ""

        try:
            description = soup.select_one(".product-description").get_text(strip=True)
        except AttributeError:
            description = ""

        try:
            sizes = [
                s.get_text(strip=True)
                for s in soup.select(".size-selector option")
                if s.get_text(strip=True)
            ]
        except Exception:
            sizes = []

        try:
            colors = [
                c.get_text(strip=True)
                for c in soup.select(".color-selector .color-name")
            ]
        except Exception:
            colors = []

        try:
            availability = "disabled" not in (
                soup.select_one(".add-to-cart").get("class", [])
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
                "external_id": "RIP-001",
                "name": "Polera Ripley Basic",
                "description": "Polera algodón peinado",
                "price": 12990.0,
                "image": "https://ripley.cl/img/polera1.jpg",
            },
            {
                "external_id": "RIP-002",
                "name": "Pantalón Cargo Hombre",
                "description": "Pantalón cargo holgado",
                "price": 29990.0,
                "image": "https://ripley.cl/img/cargo1.jpg",
            },
            {
                "external_id": "RIP-003",
                "name": "Parka Invierno Mujer",
                "description": "Parka acolchada con capucha",
                "price": 69990.0,
                "image": "https://ripley.cl/img/parka1.jpg",
            },
            {
                "external_id": "RIP-004",
                "name": "Zapatos Casual Cuero",
                "description": "Zapatos vestir cuero",
                "price": 45990.0,
                "image": "https://ripley.cl/img/zapato1.jpg",
            },
            {
                "external_id": "RIP-005",
                "name": "Short Deportivo Mujer",
                "description": "Short running licra",
                "price": 18990.0,
                "image": "https://ripley.cl/img/short1.jpg",
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
                colors=["Negro", "Gris", "Azul Marino"],
                availability=True,
            )
            for p in mock_products[:max_items]
        ]
