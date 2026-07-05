"""Base class for Playwright-based scrapers.

Resolves the core problem: requests + BeautifulSoup cannot execute JavaScript,
so all existing scrapers return mock data. Playwright renders full pages including
JS-driven product catalogs, lazy loading, and API interception.

Usage:
    class ZaraScraper(PlaywrightScraper):
        def scrape(self, category, max_items):
            page = self._new_page()
            page.goto(f"{self.base_url}/cl/{category}")
            # ... parse products
            page.close()
"""

from abc import abstractmethod
from typing import List
import logging

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from scrapers.base_scraper import BaseScraper
from models.product_dto import ProductDTO

logger = logging.getLogger(__name__)


class PlaywrightScraper(BaseScraper):
    """Scraper base using Playwright for JS-rendered e-commerce sites."""

    def __init__(self, store_name: str, base_url: str):
        super().__init__(store_name, base_url)
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    def _ensure_browser(self):
        """Lazily initialize Playwright browser (shared across calls)."""
        if self._browser is None or not self._browser.is_connected():
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--single-process",
                ],
            )
            self._context = self._browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="es-CL",
                timezone_id="America/Santiago",
                extra_http_headers={
                    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
                },
            )
            # Apply stealth init script
            self._context.add_init_script(STEALTH_JS)
            logger.info("Playwright browser initialized for %s", self._store_name)

    def _new_page(self) -> Page:
        """Create a new page with resource blocking for performance."""
        self._ensure_browser()
        page = self._context.new_page()

        # Block heavy resources that aren't needed for scraping
        page.route(
            "**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,otf}",
            lambda route: route.abort(),
        )
        page.route("**/analytics**", lambda route: route.abort())
        page.route("**/tracking**", lambda route: route.abort())
        page.route("**/gtag**", lambda route: route.abort())
        page.route("**/google-analytics**", lambda route: route.abort())
        page.route("**/hotjar**", lambda route: route.abort())
        page.route("**/sentry**", lambda route: route.abort())

        return page

    def _scroll_to_load(self, page: Page, scrolls: int = 3, delay_ms: int = 1500):
        """Scroll page to trigger lazy loading of products."""
        for _ in range(scrolls):
            page.evaluate("window.scrollBy(0, 1000)")
            page.wait_for_timeout(delay_ms)

    def _wait_for_products(self, page: Page, timeout_ms: int = 10000):
        """Wait for product elements to appear in DOM."""
        selectors = [
            "[data-articleid]",
            "[data-product-id]",
            ".product-card",
            ".product-grid-item",
            "[data-pod]",
            ".pod-item",
            ".js-product",
            "[data-product-name]",
        ]
        for sel in selectors:
            try:
                page.wait_for_selector(sel, timeout=timeout_ms // len(selectors))
                return sel
            except Exception:
                continue
        return None

    @abstractmethod
    def scrape(self, category: str, max_items: int) -> List[ProductDTO]:
        """Scrape products from the store. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def parse_product(self, element_or_data) -> ProductDTO:
        """Parse a single product from DOM element or API response."""
        pass

    def close(self):
        """Clean up browser resources."""
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception as e:
            logger.warning("Error closing Playwright: %s", e)
        finally:
            self._browser = None
            self._context = None
            self._playwright = None

    def __del__(self):
        self.close()


# Stealth script to bypass bot detection
STEALTH_JS = """
// Override webdriver property
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
});

// Override plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});

// Override languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['es-CL', 'es', 'en'],
});

// Chrome runtime
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {},
};

// Permissions
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) =>
    parameters.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : originalQuery(parameters);

// WebGL vendor/renderer
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Intel Inc.';
    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
    return getParameter.apply(this, arguments);
};
"""
