import re
from abc import ABC, abstractmethod
from typing import List

from scrapers.models.product_dto import ProductDTO


class BaseScraper(ABC):

    def __init__(self, store_name: str, base_url: str):
        self._store_name = store_name
        self._base_url = base_url

    @property
    def store_name(self) -> str:
        return self._store_name

    @property
    def base_url(self) -> str:
        return self._base_url

    @abstractmethod
    def scrape(self, category: str, max_items: int) -> List[ProductDTO]:
        pass

    @abstractmethod
    def parse_product(self, html: str) -> ProductDTO:
        pass

    def normalize_price(self, price_str: str) -> float:
        cleaned = re.sub(r'[^\d.,]', '', price_str)
        cleaned = cleaned.replace('.', '').replace(',', '.')
        return float(cleaned)

    def _build_mock_products(self, mock_data: list[dict], category: str, max_items: int) -> List[ProductDTO]:
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
                sizes=p.get("sizes", ["S", "M", "L", "XL"]),
                colors=p.get("colors", ["Negro", "Blanco"]),
                availability=True,
            )
            for p in mock_data[:max_items]
        ]
