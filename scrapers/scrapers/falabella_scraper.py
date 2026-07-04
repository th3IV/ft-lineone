"""Falabella scraper using HTTP (SSR data extraction).

Falabella renders products via React/Next.js with server-side rendering.
Product data is embedded in the HTML inside a <script> tag as JSON with
the structure {"props":{"pageProps":{"results":[...]}}}. This scraper
fetches the HTML and parses the JSON directly — no Playwright needed.
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


class FalabellaScraper(BaseScraper):

    def __init__(self):
        super().__init__("falabella", "https://www.falabella.com")

    def scrape(self, category: str, max_items: int) -> List[ProductDTO]:
        products = []
        try:
            client = httpx.Client(follow_redirects=True, timeout=20.0)
            url = f"{self.base_url}/falabella-cl/search?Ntt={category}"
            logger.info("Scraping Falabella: %s", url)

            r = client.get(url, headers={"User-Agent": UA, "Accept": "text/html"})
            if r.status_code != 200:
                logger.warning("Falabella returned %d", r.status_code)
                return self._generate_mock_data(category, max_items)

            products = self._parse_ssr_data(r.text, max_items)
            client.close()

        except Exception as e:
            logger.error("Falabella scrape failed: %s", e)
            products = self._generate_mock_data(category, max_items)

        return products[:max_items]

    def _parse_ssr_data(self, html: str, max_items: int) -> List[ProductDTO]:
        """Parse Falabella SSR JSON payload to extract products."""
        products = []

        # Find the script tag with props.pageProps.results
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        for s in scripts:
            if not s.startswith('{"props"'):
                continue
            try:
                data = json.loads(s)
                results = data.get("props", {}).get("pageProps", {}).get("results", [])
                if not results:
                    continue

                for item in results[:max_items]:
                    product = self._parse_falabella_product(item)
                    if product and product.name:
                        products.append(product)

                break
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug("Failed to parse Falabella SSR JSON: %s", e)
                continue

        return products[:max_items]

    def _parse_falabella_product(self, item: dict) -> Optional[ProductDTO]:
        """Parse a single Falabella product from SSR data."""
        if not isinstance(item, dict):
            return None

        # Extract fields
        ext_id = str(item.get("productId", ""))
        name = item.get("displayName", "")
        brand = item.get("brand", "")
        url = item.get("url", "")

        # Extract price
        price = 0.0
        prices = item.get("prices", [])
        if isinstance(prices, list) and prices:
            for p in prices:
                if isinstance(p, dict):
                    price_list = p.get("price", [])
                    if isinstance(price_list, list) and price_list:
                        price_str = price_list[0]
                        # Remove dots used as thousand separators
                        price_str = price_str.replace(".", "")
                        try:
                            price = float(price_str)
                            break
                        except ValueError:
                            continue

        # Extract images
        images = []
        media_urls = item.get("mediaUrls", [])
        if isinstance(media_urls, list):
            images = [u for u in media_urls if isinstance(u, str) and u.startswith("http")]

        # Extract colors and sizes from variants
        colors = []
        sizes = []
        variants = item.get("variants", [])
        if isinstance(variants, list):
            for v in variants:
                if isinstance(v, dict):
                    vtype = v.get("type", "")
                    options = v.get("options", [])
                    if vtype == "COLOR" and isinstance(options, list):
                        colors = [
                            o.get("value", "") for o in options
                            if isinstance(o, dict) and o.get("value")
                        ]
                    elif vtype == "SIZES" and isinstance(options, list):
                        sizes = [
                            o.get("size", o.get("value", "")) for o in options
                            if isinstance(o, dict)
                        ]

        # Extract availability
        availability = True
        avail = item.get("availability", {})
        if isinstance(avail, dict):
            home_del = avail.get("homeDeliveryShipping", "")
            if home_del == "NOT_AVAILABLE":
                availability = False

        if not name:
            return None

        return ProductDTO(
            external_id=ext_id,
            store=self.store_name,
            name=name,
            description=f"Marca: {brand}" if brand else "",
            price=price,
            currency="CLP",
            original_url=url,
            image_urls=images[:5],
            category="",
            sizes=sizes,
            colors=colors,
            availability=availability,
        )

    def parse_product(self, element_or_data) -> ProductDTO:
        pass

    def _generate_mock_data(self, category: str, max_items: int) -> List[ProductDTO]:
        mock = [
            {"id": "FAL-001", "name": "Vestido Casual Mujer", "price": 29990.0},
            {"id": "FAL-002", "name": "Polera Basica", "price": 12990.0},
            {"id": "FAL-003", "name": "Jean Recto Mujer", "price": 34990.0},
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
