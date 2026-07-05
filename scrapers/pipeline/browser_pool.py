"""Browser pool for sharing Playwright browser instances across scrapers.

Avoids the overhead of launching a new browser for each store scrape.
Limits concurrent browser instances to prevent resource exhaustion.

Usage:
    pool = BrowserPool.get_instance()
    browser = pool.acquire()
    try:
        page = browser.new_page()
        # ... scrape
    finally:
        pool.release()
"""

import logging
import threading
from typing import Optional

from playwright.sync_api import sync_playwright, Browser

logger = logging.getLogger(__name__)


class BrowserPool:
    """Singleton pool of shared Playwright browser instances."""

    _instance: Optional["BrowserPool"] = None
    _lock = threading.Lock()

    def __init__(self, max_browsers: int = 3):
        self._max_browsers = max_browsers
        self._browsers: list[Browser] = []
        self._available: list[Browser] = []
        self._pw = None
        self._pool_lock = threading.Lock()

    @classmethod
    def get_instance(cls, max_browsers: int = 3) -> "BrowserPool":
        """Get or create the singleton pool instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(max_browsers)
        return cls._instance

    def _create_browser(self) -> Browser:
        """Create a new Playwright Chromium browser."""
        if self._pw is None:
            self._pw = sync_playwright().start()

        browser = self._pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ],
        )
        logger.info("Created new browser instance (total: %d)", len(self._browsers) + 1)
        return browser

    def acquire(self) -> Browser:
        """Acquire a browser from the pool. Creates new if pool is empty."""
        with self._pool_lock:
            # Try to reuse an existing browser
            if self._available:
                browser = self._available.pop()
                if browser.is_connected():
                    return browser
                # Browser disconnected, remove and create new
                self._browsers.remove(browser)
                try:
                    browser.close()
                except Exception:
                    pass

            # Create new if under limit
            if len(self._browsers) < self._max_browsers:
                browser = self._create_browser()
                self._browsers.append(browser)
                return browser

            # Pool exhausted — wait for one to become available
            logger.warning("Browser pool exhausted, waiting...")
            # Simple spin wait (could use condition variable for production)
            import time
            for _ in range(100):
                time.sleep(0.5)
                if self._available:
                    return self.acquire()

            raise RuntimeError("Browser pool exhausted and no instances available")

    def release(self, browser: Browser):
        """Return a browser to the pool for reuse."""
        with self._pool_lock:
            if browser.is_connected() and browser not in self._available:
                self._available.append(browser)

    def close_all(self):
        """Shut down all browser instances."""
        with self._pool_lock:
            for browser in self._browsers:
                try:
                    browser.close()
                except Exception:
                    pass
            self._browsers.clear()
            self._available.clear()
            if self._pw:
                self._pw.stop()
                self._pw = None
            logger.info("All browsers closed")

    def stats(self) -> dict:
        """Return pool statistics."""
        return {
            "total": len(self._browsers),
            "available": len(self._available),
            "in_use": len(self._browsers) - len(self._available),
            "max": self._max_browsers,
        }
