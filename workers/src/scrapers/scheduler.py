"""Scraper scheduler for Cloudflare Workers Cron Triggers."""

import asyncio
from datetime import datetime, timezone

from scrapers.zara import ZaraScraper
from scrapers.paris import ParisScraper
from scrapers.maui import MauiScraper
from scrapers.falabella import FalabellaScraper
from scrapers.hm import HMScraper
from scrapers.fashionpark import FashionParkScraper
from services.database import DatabaseService


# Rate limiting: seconds between requests per store
RATE_LIMITS = {
    "paris": 1.5,
    "maui": 2.0,
    "zara": 3.0,
    "falabella": 1.5,
    "hm": 1.5,
    "fashionpark": 1.0,
}

# Real categories/search terms per store
STORE_CATEGORIES = {
    "paris": {
        "type": "search",  # Paris uses search queries
        "queries": [
            "polera mujer",
            "jean mujer",
            "polera hombre",
            "vestido mujer",
            "chaqueta hombre",
            "falda mujer",
        ],
    },
    "maui": {
        "type": "category",  # Maui uses category slugs
        "categories": [
            "hombre-poleras",
            "mujer-poleras",
            "mujer-camisas",
            "mujer-pantalones",
            "mujer-vestidos",
            "hombre-polerones",
        ],
    },
    "zara": {
        "type": "category",  # Zara uses category slugs
        "categories": [
            "mujer",
            "hombre",
        ],
    },
    "falabella": {
        "type": "search",  # Falabella uses search queries
        "queries": [
            "polera mujer",
            "polera hombre",
            "jean mujer",
            "jean hombre",
            "vestido mujer",
            "chaqueta mujer",
        ],
    },
    "hm": {
        "type": "search",  # H&M uses VTEX catalog_system search
        "queries": [
            "polera",
            "jean",
            "vestido",
            "chaqueta",
            "falda",
            "poleron",
        ],
    },
    "fashionpark": {
        "type": "search",  # Fashion Park uses Shopify search
        "queries": [
            "polera mujer",
            "polera hombre",
            "jean mujer",
            "jean hombre",
            "vestido mujer",
            "chaqueta mujer",
        ],
    },

}


class ScraperRunner:
    """Runs scrapers on a schedule via Cloudflare Workers Cron."""

    def __init__(self, env, max_products=30):
        self.env = env
        self.db = DatabaseService(env)
        self.max_products = max_products
        self.scrapers = {
            "zara": ZaraScraper(),
            "paris": ParisScraper(),
            "maui": MauiScraper(),
            "falabella": FalabellaScraper(),
            "hm": HMScraper(),
            "fashionpark": FashionParkScraper(),
        }

    async def run_all_scrapers(self, max_concurrent: int = 3) -> dict:
        """Run all scrapers in parallel batches and return results."""
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scrapers": {},
        }

        async def run_one(store_name: str, scraper):
            try:
                return store_name, await self._run_scraper(store_name, scraper)
            except Exception as e:
                return store_name, {"status": "error", "error": str(e)}

        # Run scrapers in parallel batches to avoid CPU timeout
        items = list(self.scrapers.items())
        for i in range(0, len(items), max_concurrent):
            batch = items[i:i + max_concurrent]
            batch_results = await asyncio.gather(*[run_one(name, scraper) for name, scraper in batch])
            for store_name, result in batch_results:
                results["scrapers"][store_name] = result

        return results

    async def _run_scraper(self, store_name: str, scraper) -> dict:
        """Run a single scraper and return results."""
        start_time = datetime.now(timezone.utc)
        rate_limit = RATE_LIMITS.get(store_name, 2.0)
        store_config = STORE_CATEGORIES.get(store_name, {})

        total_products = 0
        total_new = 0
        total_skipped = 0
        total_errors = 0

        try:
            if store_config.get("type") == "search":
                # Paris: search by queries
                queries = store_config.get("queries", [])
                for query in queries:
                    try:
                        products = await scraper.search_products(query, max_items=self.max_products)
                        if len(products) < 5:
                            print(f"[{store_name}] Query '{query}' returned only {len(products)} products (min 5)")
                        total_products += len(products)
                        for product in products:
                            try:
                                result = await self._ingest_product(store_name, product)
                                if result["status"] == "created":
                                    total_new += 1
                                elif result["status"] == "error":
                                    total_errors += 1
                                    print(f"[{store_name}] Ingest error: {result.get('error')} for {result.get('product_name')}")
                                else:
                                    total_skipped += 1
                            except Exception as e:
                                total_errors += 1
                                print(f"[{store_name}] Exception: {e}")
                        await asyncio.sleep(rate_limit)
                    except Exception:
                        total_errors += 1
            else:
                # Maui/Zara: scrape by categories
                categories = store_config.get("categories", [])
                for category in categories:
                    try:
                        products = await scraper.scrape_category(category, max_items=self.max_products)
                        if len(products) < 5:
                            print(f"[{store_name}] Category '{category}' returned only {len(products)} products (min 5)")
                        total_products += len(products)
                        for product in products:
                            try:
                                result = await self._ingest_product(store_name, product)
                                if result["status"] == "created":
                                    total_new += 1
                                elif result["status"] == "error":
                                    total_errors += 1
                                    print(f"[{store_name}] Ingest error: {result.get('error')} for {result.get('product_name')}")
                                else:
                                    total_skipped += 1
                            except Exception as e:
                                total_errors += 1
                                print(f"[{store_name}] Exception: {e}")
                        await asyncio.sleep(rate_limit)
                    except Exception:
                        total_errors += 1

            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            return {
                "status": "completed",
                "total_products": total_products,
                "new_products": total_new,
                "skipped_products": total_skipped,
                "errors": total_errors,
                "duration_seconds": round(duration, 1),
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def _ingest_product(self, store_name: str, product) -> dict:
        """Ingest a scraped product into the database."""
        # Use cached existing products set to avoid repeated DB queries
        if not hasattr(self, '_existing_ids'):
            self._existing_ids = {}
        if store_name not in self._existing_ids:
            existing_products, _ = await self.db.get_products(
                {"store": store_name},
                page=1,
                limit=2000,
            )
            self._existing_ids[store_name] = {p.external_id: p.id for p in existing_products}

        if product.external_id in self._existing_ids[store_name]:
            return {"status": "skipped", "product_id": self._existing_ids[store_name][product.external_id]}

        # Create new product
        try:
            image_urls = getattr(product, "image_urls", None) or ([product.image_url] if product.image_url else [])
            created = await self.db.create_product(
                {
                    "external_id": product.external_id,
                    "name": product.name,
                    "store": store_name,
                    "price": product.price,
                    "currency": product.currency,
                    "category": product.category,
                    "description": product.description,
                    "original_url": product.original_url,
                    "image_url": product.image_url,
                    "image_urls": image_urls,
                    "sizes": product.sizes,
                    "colors": product.colors,
                    "availability": product.availability,
                }
            )
            self._existing_ids[store_name][product.external_id] = created.id
            return {"status": "created", "product_id": created.id}
        except Exception as e:
            return {"status": "error", "error": str(e), "product_name": product.name}

    async def close(self):
        """Close all scrapers."""
        for scraper in self.scrapers.values():
            await scraper.close()
