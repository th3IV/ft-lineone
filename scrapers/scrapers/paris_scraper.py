"""Paris scraper using HTTP (SSR data extraction).

Paris.cl renders products via React Server Components. Product data is
embedded in the HTML as serialized RSC payload inside <script> tags.
LD+JSON structured data is embedded inside RSC push scripts with escaped quotes.

This scraper:
1. Finds RSC push scripts containing itemListElement (product list)
2. Unescapes the JSON and parses product data
"""

import json
import logging
import re
from typing import List, Optional

import httpx

from scrapers.base_scraper import BaseScraper
from models.product_dto import ProductDTO

logger = logging.getLogger(__name__)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


class ParisScraper(BaseScraper):

    def __init__(self):
        super().__init__("paris", "https://www.paris.cl")

    def scrape(self, category: str, max_items: int) -> List[ProductDTO]:
        products = []
        try:
            client = httpx.Client(follow_redirects=True, timeout=20.0)
            url = f"{self.base_url}/search?q={category}"
            logger.info("Scraping Paris: %s", url)

            r = client.get(url, headers={"User-Agent": UA, "Accept": "text/html"})
            if r.status_code != 200:
                logger.warning("Paris returned %d", r.status_code)
                return self._generate_mock_data(category, max_items)

            products = self._parse_ssr_data(r.text, max_items)
            client.close()

        except Exception as e:
            logger.error("Paris scrape failed: %s", e)
            products = self._generate_mock_data(category, max_items)

        return products[:max_items]

    def _parse_ssr_data(self, html: str, max_items: int) -> List[ProductDTO]:
        """Parse Paris.cl SSR RSC payload to extract products."""
        products = []

        # Find RSC push scripts containing itemListElement
        scripts = re.findall(
            r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', html, re.DOTALL
        )

        for script in scripts:
            if "itemListElement" not in script:
                continue

            try:
                # The script content starts with the LD+JSON object
                # Find the JSON start (first {)
                json_start = script.find("{")
                if json_start < 0:
                    continue

                raw = script[json_start:]

                # Unescape the content
                content = raw.replace('\\"', '"')
                content = content.replace("\\/", "/")
                content = content.replace("\\\\", "\\")

                # Parse the JSON
                data = json.loads(content)

                # Navigate to itemListElement
                items = data.get("mainEntity", {}).get("itemListElement", [])
                for item in items:
                    product_data = item.get("item", {})
                    if not product_data or product_data.get("@type") != "Product":
                        continue

                    name = product_data.get("name", "")
                    url = product_data.get("url", "")
                    image = product_data.get("image", "")
                    sku = product_data.get("sku", "")

                    # Extract price from offers
                    price = 0.0
                    offers = product_data.get("offers", {})
                    if isinstance(offers, dict):
                        price_val = offers.get("price", 0)
                        try:
                            price = float(price_val)
                        except (ValueError, TypeError):
                            pass

                    # Extract brand
                    brand = ""
                    brand_data = product_data.get("brand", {})
                    if isinstance(brand_data, dict):
                        brand = brand_data.get("name", "")

                    if name:
                        products.append(ProductDTO(
                            external_id=str(sku) if sku else "",
                            store=self.store_name,
                            name=name,
                            description=f"Marca: {brand}" if brand else "",
                            price=price,
                            currency="CLP",
                            original_url=url,
                            image_urls=[image] if image else [],
                            category="",
                            sizes=[],
                            colors=[],
                            availability=True,
                        ))

                break  # Found the product list, no need to continue

            except (json.JSONDecodeError, KeyError) as e:
                logger.debug("Failed to parse LD+JSON block: %s", e)
                continue

        return products

    def parse_product(self, element_or_data) -> ProductDTO:
        pass

    def _generate_mock_data(self, category: str, max_items: int) -> List[ProductDTO]:
        mock = [
            {"id": "PAR-001", "name": "Polera Basica", "price": 9990.0},
            {"id": "PAR-002", "name": "Jeans Mom Fit", "price": 29990.0},
            {"id": "PAR-003", "name": "Vestido Casual", "price": 39990.0},
        ]
        return [
            ProductDTO(
                external_id=p["id"], store=self.store_name, name=p["name"],
                description="", price=p["price"], currency="CLP",
                original_url="", image_urls=[], category=category,
                sizes=["S", "M", "L"], colors=["Negro", "Blanco"], availability=True,
            )
            for p in mock[:max_items]
        ]
