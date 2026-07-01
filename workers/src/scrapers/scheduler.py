"""Scraper scheduler for Cloudflare Workers Cron Triggers."""

import asyncio
from datetime import datetime

from scrapers.zara import ZaraScraper
from scrapers.paris import ParisScraper
from scrapers.maui import MauiScraper
from services.database import DatabaseService


class ScraperRunner:
    """Runs scrapers on a schedule via Cloudflare Workers Cron."""

    def __init__(self, env):
        self.env = env
        self.db = DatabaseService(env)
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
            categories = self._get_categories(store_name)

            total_products = 0
            total_new = 0
            total_skipped = 0
            total_errors = 0

            for category in categories:
                try:
                    products = await self._scrape_category(store_name, scraper, category)
                    total_products += len(products)

                    for product in products:
                        try:
                            result = await self._ingest_product(store_name, product)
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
            return {"status": "failed", "error": str(e)}

    async def _scrape_category(self, store_name: str, scraper, category: str) -> list:
        """Scrape products from a category (all scrapers are now async)."""
        if store_name == "zara":
            return await scraper.scrape_category(category, max_items=50)
        elif store_name == "paris":
            return await scraper.scrape_category(category, max_items=50)
        elif store_name == "maui":
            return await scraper.scrape_category(category, max_items=50)
        else:
            return []

    async def _ingest_product(self, store_name: str, product) -> dict:
        """Ingest a scraped product into the database."""
        existing_products, _ = await self.db.get_products(
            {"store": store_name}, page=1, limit=1000,
        )

        for p in existing_products:
            if p.external_id == product.external_id:
                return {"status": "skipped", "product_id": p.id}

        created = await self.db.create_product({
            "external_id": product.external_id,
            "name": product.name,
            "store": store_name,
            "price": product.price,
            "currency": product.currency,
            "category": product.category,
            "description": product.description,
            "original_url": product.original_url,
            "image_url": product.image_url,
            "image_urls": [product.image_url] if product.image_url else [],
            "sizes": product.sizes,
            "colors": product.colors,
            "availability": product.availability,
        })

        return {"status": "created", "product_id": created.id}

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

    async def close(self):
        """Close all scrapers."""
        for scraper in self.scrapers.values():
            await scraper.close()
