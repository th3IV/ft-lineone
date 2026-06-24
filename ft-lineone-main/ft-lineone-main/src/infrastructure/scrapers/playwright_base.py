import os
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class PlaywrightScraperHelper:
    """Manages a Playwright browser instance for WAF-protected stores."""

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        self._started = False

    @property
    def is_started(self) -> bool:
        return self._started

    async def start(self):
        if self._started:
            return
        from playwright.async_api import async_playwright
        self._playwright = await async_playwright().start()
        chrome_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        chrome_exists = os.path.exists(chrome_path)

        launch_kwargs = {
            "headless": not chrome_exists,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-web-security",
            ],
        }
        if chrome_exists:
            launch_kwargs["executable_path"] = chrome_path
            logger.info("Usando Chrome del sistema: %s", chrome_path)
        else:
            logger.info("Usando Chromium de Playwright (headless)")

        self._browser = await self._playwright.chromium.launch(**launch_kwargs)
        self._context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="es-CL",
        )
        self._started = True

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._started = False

    async def extract_products(
        self,
        url: str,
        card_selector: str = "li._product",
        max_items: int = 20,
        timeout: int = 30000,
    ) -> List[Dict[str, Any]]:
        if not self._started:
            await self.start()

        page = await self._context.new_page()
        try:
            logger.info("Navegando a: %s", url)
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            await page.wait_for_timeout(3000)

            cards = await page.query_selector_all(card_selector)
            logger.info("Productos encontrados: %d", len(cards))

            products = []
            for card in cards[:max_items]:
                try:
                    product = await self._extract_card(card)
                    if product and product.get("name") and product.get("price", 0) > 0:
                        products.append(product)
                except Exception as e:
                    logger.warning("Error extrayendo producto: %s", e)
                    continue

            return products
        finally:
            await page.close()

    async def _extract_card(self, card) -> Dict[str, Any] | None:
        product_id = await card.get_attribute("data-productid")
        product_key = await card.get_attribute("data-productkey")

        link_el = await card.query_selector("a")
        product_url = ""
        if link_el:
            product_url = await link_el.get_attribute("href") or ""

        name = ""
        name_el = await card.query_selector("h2, h3, [class*=name], [class*=title]")
        if name_el:
            name = (await name_el.inner_text()).strip()

        if not name and link_el:
            name = (await link_el.get_attribute("title")) or ""

        price = 0.0
        price_el = await card.query_selector("[class*=price], span[class*=currency]")
        if price_el:
            price_text = (await price_el.inner_text()).strip()
            price = self._parse_price(price_text)

        image_url = ""
        img = await card.query_selector("img")
        if img:
            image_url = (await img.get_attribute("src")) or (await img.get_attribute("data-src")) or ""

        if not product_id:
            return None

        return {
            "external_id": f"zar-{product_id}",
            "name": name,
            "price": price,
            "currency": "CLP",
            "image_url": image_url,
            "product_url": f"https://www.zara.com{product_url}" if product_url and product_url.startswith("/") else product_url,
        }

    def _parse_price(self, price_text: str) -> float:
        cleaned = re.sub(r"[^\d.,]", "", price_text)
        cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
