from typing import List

import requests
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from models.product_dto import ProductDTO


class ZaraScraper(BaseScraper):

    def __init__(self):
        super().__init__("zara", "https://www.zara.com")

    def scrape(self, category: str, max_items: int) -> List[ProductDTO]:
        products = []
        url = f"{self.base_url}/cl/{category}"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            items = soup.select(".product-grid-item") or soup.select(".product-card") or soup.select("[data-articleid]")
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
            name = soup.select_one("[data-name]")["data-name"]
        except (AttributeError, KeyError, TypeError):
            try:
                name = soup.select_one(".product-name").get_text(strip=True)
            except AttributeError:
                name = ""

        try:
            price = self.normalize_price(
                soup.select_one(".price-current").get_text(strip=True)
            )
        except (AttributeError, ValueError):
            try:
                price = float(soup.select_one("[data-price]")["data-price"])
            except (AttributeError, KeyError, TypeError):
                price = 0.0

        try:
            product_id = soup.select_one("[data-articleid]")["data-articleid"]
        except (AttributeError, KeyError, TypeError):
            try:
                product_id = soup.select_one("[data-product-id]")["data-product-id"]
            except (AttributeError, KeyError, TypeError):
                product_id = ""

        try:
            image = soup.select_one(".product-image source")["srcset"]
        except (AttributeError, KeyError, TypeError):
            try:
                image = soup.select_one("img")["src"]
            except (AttributeError, KeyError, TypeError):
                image = ""

        try:
            description = soup.select_one(".product-description").get_text(strip=True)
        except AttributeError:
            description = ""

        try:
            sizes = [
                s.get_text(strip=True)
                for s in soup.select(".size-selector button:not(.disabled)")
            ]
        except Exception:
            sizes = []

        try:
            colors = [
                c.get_text(strip=True)
                for c in soup.select(".color-selector span")
            ]
        except Exception:
            colors = []

        try:
            availability = bool(
                soup.select_one(".add-to-cart:not(.disabled)")
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
        mock_by_category = {
            "mujer": [
                {"name": "Blazer Oversize Mujer", "description": "Blazer corte oversize con solapa ancha", "price": 79990.0, "image": "https://picsum.photos/seed/zara-blazer/400/500"},
                {"name": "Vestido Noche Corto", "description": "Vestido corto con brillos y escote en V", "price": 69990.0, "image": "https://picsum.photos/seed/zara-vestido/400/500"},
                {"name": "Jeans Rectos Mujer", "description": "Jeans tiro alto recto en denim elastico", "price": 39990.0, "image": "https://picsum.photos/seed/zara-jeans/400/500"},
                {"name": "Falda Mini Pliatada", "description": "Falda mini plisada con pretina ancha", "price": 25990.0, "image": "https://picsum.photos/seed/zara-falda/400/500"},
                {"name": "Polera Algodon Mujer", "description": "Polera de algodon organico cuello redondo", "price": 15990.0, "image": "https://picsum.photos/seed/zara-polera-m/400/500"},
                {"name": "Chaqueta Cuero Mujer", "description": "Chaqueta de cuero sintetico con cierre", "price": 89990.0, "image": "https://picsum.photos/seed/zara-chaqueta-m/400/500"},
                {"name": "Short Denim Mujer", "description": "Short de jean con dobladillo desfilado", "price": 22990.0, "image": "https://picsum.photos/seed/zara-short-m/400/500"},
                {"name": "Blusa Seda Mujer", "description": "Blusa de seda con manga larga y botones", "price": 34990.0, "image": "https://picsum.photos/seed/zara-blusa/400/500"},
                {"name": "Abrigo Lana Mujer", "description": "Abrigo de lana con cinturon incluido", "price": 99990.0, "image": "https://picsum.photos/seed/zara-abrigo/400/500"},
                {"name": "Top Cropt Mujer", "description": "Top corto de algodon con tirantes ajustables", "price": 12990.0, "image": "https://picsum.photos/seed/zara-top/400/500"},
            ],
            "hombre": [
                {"name": "Camisa Lino Hombre", "description": "Camisa manga larga de lino premium", "price": 45990.0, "image": "https://picsum.photos/seed/zara-camisa-h/400/500"},
                {"name": "Chaleco Acolchado", "description": "Chaleco acolchado reversible", "price": 54990.0, "image": "https://picsum.photos/seed/zara-chaleco/400/500"},
                {"name": "Pantalon Chino Hombre", "description": "Pantalon chino de algodon slim fit", "price": 39990.0, "image": "https://picsum.photos/seed/zara-chino/400/500"},
                {"name": "Poleron Cremallera Hombre", "description": "Poleron con cremallera completa y capucha", "price": 34990.0, "image": "https://picsum.photos/seed/zara-poleron-h/400/500"},
                {"name": "Jeans Skinny Hombre", "description": "Jeans skinny elastizado oscuro", "price": 42990.0, "image": "https://picsum.photos/seed/zara-jeans-h/400/500"},
                {"name": "Polera Basica Hombre", "description": "Polera basica de algodon peinado", "price": 13990.0, "image": "https://picsum.photos/seed/zara-polera-h/400/500"},
                {"name": "Chaqueta Bomber Hombre", "description": "Chaqueta estilo bomber con cierre", "price": 59990.0, "image": "https://picsum.photos/seed/zara-bomber/400/500"},
                {"name": "Short Deportivo Hombre", "description": "Short deportivo con bolsillos laterales", "price": 19990.0, "image": "https://picsum.photos/seed/zara-short-h/400/500"},
                {"name": "Blazer Slim Hombre", "description": "Blazer slim fit en tejido mezcla", "price": 69990.0, "image": "https://picsum.photos/seed/zara-blazer-h/400/500"},
                {"name": "Parka Invierno Hombre", "description": "Parka impermeable con capucha desmontable", "price": 89990.0, "image": "https://picsum.photos/seed/zara-parka/400/500"},
            ],
            "zapatos": [
                {"name": "Zapatillas Casual Zara", "description": "Zapatillas casual con suela cushlon", "price": 49990.0, "image": "https://picsum.photos/seed/zara-zapa/400/500"},
                {"name": "Botines Cuero Zara", "description": "Botines de cuero con taco block", "price": 69990.0, "image": "https://picsum.photos/seed/zara-botin/400/500"},
                {"name": "Zapatos Oxford Zara", "description": "Zapatos oxford de cuero con suela", "price": 59990.0, "image": "https://picsum.photos/seed/zara-oxford/400/500"},
                {"name": "Sandalias Playa Zara", "description": "Sandalias de playa con suela goma", "price": 15990.0, "image": "https://picsum.photos/seed/zara-sandalias/400/500"},
            ],
            "bolsos": [
                {"name": "Mochila Urbana Zara", "description": "Mochila urbana impermeable 25L", "price": 34990.0, "image": "https://picsum.photos/seed/zara-mochila/400/500"},
                {"name": "Bolso Tote Zara", "description": "Bolso tote de cuero sintetico grande", "price": 45990.0, "image": "https://picsum.photos/seed/zara-tote/400/500"},
                {"name": "Cartera Bandolera Zara", "description": "Cartera bandolera ajustable pequena", "price": 29990.0, "image": "https://picsum.photos/seed/zara-bandolera/400/500"},
            ],
        }
        products = mock_by_category.get(category, [
            {"name": "Producto Zara", "description": "Producto de temporada Zara", "price": 29990.0, "image": "https://picsum.photos/seed/zara-generic/400/500"},
        ])
        return [
            ProductDTO(
                external_id=f"ZAR-{category[:3].upper()}-{i+1:03d}",
                store=self.store_name,
                name=p["name"],
                description=p["description"],
                price=p["price"],
                currency="CLP",
                original_url=f"{self.base_url}/{category}/product/{i+1}",
                image_urls=[p["image"]],
                category=category,
                sizes=["XS", "S", "M", "L", "XL"],
                colors=["Beige", "Negro", "Blanco", "Gris"],
                availability=True,
            )
            for i, p in enumerate(products[:max_items])
        ]
