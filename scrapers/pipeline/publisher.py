from typing import List

import httpx

from scrapers.models.product_dto import ProductDTO


class Publisher:

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)

    def publish_product(self, product: ProductDTO) -> dict:
        payload = {
            "external_id": product.external_id,
            "store": product.store,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "currency": product.currency,
            "original_url": product.original_url,
            "image_urls": product.image_urls,
            "category": product.category,
            "sizes": product.sizes,
            "colors": product.colors,
            "availability": product.availability,
        }
        response = self.client.post(
            f"{self.base_url}/api/v1/scrapers/ingest",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def publish_batch(self, products: List[ProductDTO]) -> List[dict]:
        results = []
        for product in products:
            try:
                result = self.publish_product(product)
                results.append(result)
            except httpx.HTTPError:
                results.append({"error": f"Failed to publish {product.external_id}"})
        return results

    def check_health(self) -> bool:
        try:
            response = self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def close(self):
        self.client.close()
