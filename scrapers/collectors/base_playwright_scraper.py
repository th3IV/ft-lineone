from abc import abstractmethod
from typing import List
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from scrapers.collectors.base_scraper import BaseScraper
from scrapers.models.product_dto import ProductDTO


class BasePlaywrightScraper(BaseScraper):

    def __init__(self, store_name: str, base_url: str):
        super().__init__(store_name, base_url)

    def fetch_html(self, url: str, wait_for_selector: str | None = None, timeout: int = 30000) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1280, "height": 720},
            )
            page = context.new_page()
            page.goto(url, timeout=timeout, wait_until="networkidle")
            if wait_for_selector:
                page.wait_for_selector(wait_for_selector, timeout=10000)
            html = page.content()
            browser.close()
        return html

    def parse_html(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    @abstractmethod
    def scrape(self, category: str, max_items: int) -> List[ProductDTO]:
        pass

    @abstractmethod
    def parse_product(self, html: str) -> ProductDTO:
        pass
