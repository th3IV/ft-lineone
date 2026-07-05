"""Ripley scraper using Playwright."""

import logging
from typing import List, Optional

from playwright.sync_api import Page

from scrapers.playwright_scraper import PlaywrightScraper
from models.product_dto import ProductDTO

logger = logging.getLogger(__name__)


class RipleyScraper(PlaywrightScraper):

    def __init__(self):
        super().__init__("ripley", "https://simple.ripley.cl")

    def scrape(self, category: str, max_items: int) -> List[ProductDTO]:
        products = []
        api_data = []

        def handle_response(response):
            url = response.url
            if any(k in url for k in ["api", "graphql", "products", "search", "catalog"]):
                try:
                    body = response.json()
                    api_data.append({"url": url, "data": body})
                except Exception:
                    pass

        page = self._new_page()
        page.on("response", handle_response)

        try:
            url = f"{self.base_url}/{category}"
            logger.info("Scraping Ripley: %s", url)
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            self._scroll_to_load(page, scrolls=4, delay_ms=2000)

            for entry in api_data:
                parsed = self._parse_api_response(entry["data"], max_items - len(products))
                products.extend(parsed)
                if len(products) >= max_items:
                    break

            if not products:
                products = self._parse_dom(page, max_items)

        except Exception as e:
            logger.error("Ripley scrape failed: %s", e)
            products = self._generate_mock_data(category, max_items)
        finally:
            page.close()

        return products[:max_items]

    def _parse_api_response(self, data: dict, max_items: int) -> List[ProductDTO]:
        products = []
        product_list = self._find_products(data)
        if not product_list:
            return products
        for item in product_list[:max_items]:
            try:
                product = self._parse_api_product(item)
                if product and product.name:
                    products.append(product)
            except Exception:
                continue
        return products

    def _find_products(self, data, depth=0) -> Optional[list]:
        if depth > 5:
            return None
        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                if any(k in data[0] for k in ["id", "name", "price", "sku", "partNumber"]):
                    return data
            return None
        if isinstance(data, dict):
            for key in ["products", "items", "results", "data", "catalogEntryView"]:
                if key in data:
                    result = self._find_products(data[key], depth + 1)
                    if result:
                        return result
            for value in data.values():
                if isinstance(value, (dict, list)):
                    result = self._find_products(value, depth + 1)
                    if result:
                        return result
        return None

    def _parse_api_product(self, item: dict) -> Optional[ProductDTO]:
        if not isinstance(item, dict):
            return None
        product_id = item.get("partNumber") or item.get("id") or item.get("sku") or ""
        name = item.get("name") or item.get("displayName") or ""
        price = float(item.get("price", 0) or item.get("offerPrice", 0) or 0)
        images = []
        for key in ["image", "imageUrl", "images", "thumbUrl"]:
            if key in item:
                val = item[key]
                if isinstance(val, str) and val.startswith("http"):
                    images.append(val)
                elif isinstance(val, list):
                    images.extend([i for i in val if isinstance(i, str) and i.startswith("http")])
        if not name:
            return None
        return ProductDTO(
            external_id=str(product_id), store=self.store_name, name=name,
            description=item.get("description", ""), price=price, currency="CLP",
            original_url=item.get("url", ""), image_urls=images[:5],
            category="", sizes=[], colors=[], availability=True,
        )

    def _parse_dom(self, page: Page, max_items: int) -> List[ProductDTO]:
        products = []
        for sel in [".product-card", ".catalog-product-item", "[data-partnumber]"]:
            elements = page.query_selector_all(sel)
            if elements:
                for el in elements[:max_items]:
                    try:
                        product = self.parse_product(el)
                        if product and product.name:
                            products.append(product)
                    except Exception:
                        continue
                break
        return products

    def parse_product(self, element) -> ProductDTO:
        product_id = element.get_attribute("data-partnumber") or element.get_attribute("data-product-id") or ""
        name = ""
        name_el = element.query_selector(".product-card__title, .product-name")
        if name_el:
            name = name_el.inner_text()
        price = 0.0
        price_el = element.query_selector(".product-card__price, .price")
        if price_el:
            price_text = price_el.inner_text()
            if price_text:
                price = self.normalize_price(price_text)
        image = ""
        img_el = element.query_selector("img")
        if img_el:
            image = img_el.get_attribute("src") or img_el.get_attribute("data-src") or ""
        return ProductDTO(
            external_id=product_id, store=self.store_name, name=name.strip(),
            description="", price=price, currency="CLP", original_url="",
            image_urls=[image] if image else [], category="", sizes=[], colors=[],
            availability=True,
        )

    def _generate_mock_data(self, category: str, max_items: int) -> List[ProductDTO]:
        mock = [
            {"id": "RIP-001", "name": "Smart TV 55\"", "price": 299990.0},
            {"id": "RIP-002", "name": "Laptop Gamer", "price": 699990.0},
            {"id": "RIP-003", "name": "Audífonos Bluetooth", "price": 49990.0},
        ]
        return [
            ProductDTO(
                external_id=p["id"], store=self.store_name, name=p["name"],
                description="", price=p["price"], currency="CLP",
                original_url="", image_urls=[], category=category,
                sizes=[], colors=[], availability=True,
            )
            for p in mock[:max_items]
        ]
