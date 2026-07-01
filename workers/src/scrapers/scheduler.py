"""Scraper scheduler for Cloudflare Workers Cron Triggers."""

import asyncio
from datetime import datetime
from typing import Optional

from scrapers.zara import ZaraScraper
from scrapers.paris import ParisScraper
from scrapers.maui import MauiScraper


class ScraperRunner:
    """Runs scrapers on a schedule via Cloudflare Workers Cron."""

    def __init__(self, env):
        self.env = env
        self.scrapers = {
            "zara": ZaraScraper(),
            "paris": ParisScraper(),
            "maui": MauiScraper(),
        }

    async def run_all_scrapers(self) -> dict:
        """Run all scrapers and return results."""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "scrapers": {},
        }

        for store_name, scraper in self.scrapers.items():
            try:
                result = await self._run_scraper(store_name, scraper)
                results["scrapers"][store_name] = result
            except Exception as e:
                results["scrapers"][store_name] = {
                    "status": "error",
                    "error": str(e),
                }

        return results

    async def _run_scraper(self, store_name: str, scraper) -> dict:
        """Run a single scraper and return results."""
        start_time = datetime.utcnow()

        try:
            # Get categories to scrape
            categories = self._get_categories(store_name)

            total_products = 0
            total_new = 0
            total_skipped = 0
            total_errors = 0

            for category in categories:
                try:
                    products = await self._scrape_category(
                        store_name, scraper, category
                    )
                    total_products += len(products)

                    # Ingest products
                    for product in products:
                        try:
                            result = await self._ingest_product(
                                store_name, product
                            )
                            if result["status"] == "created":
                                total_new += 1
                            else:
                                total_skipped += 1
                        except Exception:
                            total_errors += 1

                except Exception:
                    total_errors += 1

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            return {
                "status": "completed",
                "categories_scraped": len(categories),
                "total_products": total_products,
                "new_products": total_new,
                "skipped_products": total_skipped,
                "errors": total_errors,
                "duration_seconds": duration,
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
            }

    async def _scrape_category(self, store_name: str, scraper, category: str) -> list:
        """Scrape products from a category."""
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()

        if store_name == "zara":
            return await loop.run_in_executor(
                None, lambda: scraper.scrape_category(category, max_items=50)
            )
        elif store_name == "paris":
            return await loop.run_in_executor(
                None, lambda: scraper.scrape_category(category, max_items=50)
            )
        elif store_name == "maui":
            return await loop.run_in_executor(
                None, lambda: scraper.scrape_category(category, max_items=50)
            )
        else:
            return []

    async def _ingest_product(self, store_name: str, product) -> dict:
        """Ingest a scraped product into the database."""
        # This would call the API's ingest endpoint
        # For now, return a placeholder
        return {"status": "created", "product_id": "placeholder"}

    def _get_categories(self, store_name: str) -> list[str]:
        """Get categories to scrape for a store."""
        categories = {
            "zara": [
                "ropa-mujer",
                "ropa-hombre",
                "zapatos",
                "accesorios",
            ],
            "paris": [
                "mujer",
                "hombre",
                "calzado",
                "accesorios",
            ],
            "maui": [
                "hombre",
                "mujer",
                "accesorios",
            ],
        }
        return categories.get(store_name, [])

    def close(self):
        """Close all scrapers."""
        for scraper in self.scrapers.values():
            scraper.close()
