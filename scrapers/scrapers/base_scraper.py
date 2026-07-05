from abc import ABC, abstractmethod
from typing import List
import re
import requests

from models.product_dto import ProductDTO


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
    def parse_product(self, element_or_data) -> ProductDTO:
        pass

    def get_image(self, image_url: str) -> bytes:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        return response.content

    def normalize_price(self, price_str: str) -> float:
        cleaned = re.sub(r'[^\d.,]', '', price_str)
        cleaned = cleaned.replace('.', '').replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
