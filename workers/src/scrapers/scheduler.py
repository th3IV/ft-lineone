"""Scraper scheduler for Cloudflare Workers Cron Triggers."""

import asyncio
import json
from datetime import datetime, timezone, timedelta

from services.database import DatabaseService
from services.config import MIN_PRODUCTS_SCRAPED_BEFORE_CLEANUP, MIN_SCRAPE_COVERAGE_RATIO, STALE_PRODUCT_THRESHOLD_HOURS


# Rate limiting: seconds between requests per store
RATE_LIMITS = {
    "maui": 2.0,
    "zara": 3.0,
    "falabella": 1.5,
    "hm": 1.5,
    "fashionpark": 1.0,
}

# Retry config: max attempts, base delay (exponential backoff)
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 2.0

# Grace period: don't delete products younger than this
STALE_GRACE_PERIOD = timedelta(hours=2)

# Real categories/search terms per store
STORE_CATEGORIES = {
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
        from scrapers.zara import ZaraScraper
        from scrapers.maui import MauiScraper
        from scrapers.falabella import FalabellaScraper
        from scrapers.hm import HMScraper
        from scrapers.fashionpark import FashionParkScraper

        self.env = env
        self.db = DatabaseService(env)
        self.max_products = max_products
        self.scrapers = {
            "zara": ZaraScraper(),
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
        """Run a single scraper and return results.

        Uses UPSERT for zero-downtime: products are updated in-place,
        and stale products are cleaned up only after a successful scrape
        with adequate coverage (at least 50% of existing catalog or 10 absolute).
        """
        scrape_start = datetime.now(timezone.utc)
        rate_limit = RATE_LIMITS.get(store_name, 2.0)
        store_config = STORE_CATEGORIES.get(store_name, {})

        total_products = 0
        total_upserted = 0
        total_errors = 0
        empty_queries = 0
        total_queries = 0

        try:
            if store_config.get("type") == "search":
                # Search-based scrapers (Falabella, HM, FashionPark)
                queries = store_config.get("queries", [])
                for query in queries:
                    total_queries += 1
                    for attempt in range(RETRY_MAX_ATTEMPTS):
                        try:
                            products = await scraper.search_products(query, max_items=self.max_products)
                            if len(products) == 0:
                                empty_queries += 1
                            elif len(products) < 5:
                                print(f"[{store_name}] Query '{query}' returned only {len(products)} products (min 5)")
                            total_products += len(products)
                            for product in products:
                                try:
                                    result = await self._ingest_product(store_name, product)
                                    if result["status"] == "upserted":
                                        total_upserted += 1
                                    elif result["status"] == "error":
                                        total_errors += 1
                                        print(f"[{store_name}] Ingest error: {result.get('error')} for {result.get('product_name')}")
                                except Exception as e:
                                    total_errors += 1
                                    print(f"[{store_name}] Exception: {e}")
                            break  # Success — no retry needed
                        except Exception as e:
                            delay = RETRY_BASE_DELAY * (2 ** attempt)
                            print(json.dumps({
                                "event": "scraper_retry",
                                "store": store_name,
                                "query": query,
                                "attempt": attempt + 1,
                                "error": str(e),
                                "retry_in": delay,
                            }))
                            if attempt < RETRY_MAX_ATTEMPTS - 1:
                                await asyncio.sleep(delay)
                            else:
                                total_errors += 1
                                empty_queries += 1
                    await asyncio.sleep(rate_limit)
            else:
                # Category-based scrapers (Maui, Zara)
                categories = store_config.get("categories", [])
                for category in categories:
                    total_queries += 1
                    for attempt in range(RETRY_MAX_ATTEMPTS):
                        try:
                            products = await scraper.scrape_category(category, max_items=self.max_products)
                            if len(products) == 0:
                                empty_queries += 1
                            elif len(products) < 5:
                                print(f"[{store_name}] Category '{category}' returned only {len(products)} products (min 5)")
                            total_products += len(products)
                            for product in products:
                                try:
                                    result = await self._ingest_product(store_name, product)
                                    if result["status"] == "upserted":
                                        total_upserted += 1
                                    elif result["status"] == "error":
                                        total_errors += 1
                                        print(f"[{store_name}] Ingest error: {result.get('error')} for {result.get('product_name')}")
                                except Exception as e:
                                    total_errors += 1
                                    print(f"[{store_name}] Exception: {e}")
                            break  # Success — no retry needed
                        except Exception as e:
                            delay = RETRY_BASE_DELAY * (2 ** attempt)
                            print(json.dumps({
                                "event": "scraper_retry",
                                "store": store_name,
                                "category": category,
                                "attempt": attempt + 1,
                                "error": str(e),
                                "retry_in": delay,
                            }))
                            if attempt < RETRY_MAX_ATTEMPTS - 1:
                                await asyncio.sleep(delay)
                            else:
                                total_errors += 1
                                empty_queries += 1
                    await asyncio.sleep(rate_limit)

            end_time = datetime.now(timezone.utc)
            duration = (end_time - scrape_start).total_seconds()

            # Cleanup: remove stale products only if scrape completed successfully
            # with adequate coverage. Uses dynamic ratio + absolute minimum.
            deleted = 0
            if total_products > 0 and total_errors < total_products:
                existing_count = await self.db.count_products_by_store(store_name)
                coverage_ratio = total_upserted / existing_count if existing_count > 0 else 1.0
                # Block cleanup if: too few products, low coverage, or too many empty queries
                if (
                    total_upserted >= MIN_PRODUCTS_SCRAPED_BEFORE_CLEANUP
                    and coverage_ratio >= MIN_SCRAPE_COVERAGE_RATIO
                    and empty_queries < total_queries
                ):
                    deleted = await self.cleanup_stale_products(store_name, scrape_start.isoformat())
                else:
                    print(json.dumps({
                        "event": "cleanup_skipped_low_coverage",
                        "store": store_name,
                        "upserted": total_upserted,
                        "existing": existing_count,
                        "coverage_ratio": round(coverage_ratio, 2),
                        "empty_queries": empty_queries,
                        "total_queries": total_queries,
                    }))

            return {
                "status": "completed",
                "total_products": total_products,
                "upserted_products": total_upserted,
                "stale_deleted": deleted,
                "errors": total_errors,
                "empty_queries": empty_queries,
                "duration_seconds": round(duration, 1),
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _validate_product(self, product) -> bool:
        """Validate product data before inserting. Returns False if data is corrupted."""
        # 1. Name must exist and be at least 3 chars
        if not product.name or len(product.name) < 3:
            return False

        # 2. Price must be positive
        if product.price <= 0:
            return False

        # 3. Sizes must not contain product name
        for size in product.sizes:
            if product.name.lower() in size.lower():
                return False

        # 4. Colors must not contain product name
        for color in product.colors:
            if product.name.lower() in color.lower():
                return False

        # 5. Colors must not be sizes (e.g., "Polera XS", "Polera S")
        size_suffixes = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']
        for color in product.colors:
            color_upper = color.upper().strip()
            for suffix in size_suffixes:
                if color_upper.endswith(f' {suffix}') or color_upper == suffix:
                    return False

        return True

    async def _ingest_product(self, store_name: str, product) -> dict:
        """Ingest a scraped product into the database via UPSERT.

        On conflict (external_id, store): updates all fields + last_seen.
        On new product: inserts with last_seen = now.
        """
        # Validate product data before inserting
        if not self._validate_product(product):
            print(json.dumps({
                "event": "product_validation_failed",
                "store": store_name,
                "product_name": product.name,
                "sizes": product.sizes,
                "colors": product.colors,
            }))
            return {"status": "invalid", "product_name": product.name}

        # Upsert product (handles both new and existing)
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
            return {"status": "upserted", "product_id": created.id}
        except Exception as e:
            return {"status": "error", "error": str(e), "product_name": product.name}

    async def cleanup_stale_products(self, store_name: str, scrape_start_time: str):
        """Remove products not seen in the last 48 hours (multi-run threshold).

        Uses STALE_PRODUCT_THRESHOLD_HOURS so products aren't deleted just because
        a single scrape run didn't cover them (e.g. max_products caps).
        The scrape_start_time parameter is kept for API compatibility but
        the actual deletion uses the 48h cutoff from config.
        """
        try:
            result = await self.db.delete_stale_products(
                store_name,
                scrape_start_time,
                stale_hours=STALE_PRODUCT_THRESHOLD_HOURS,
            )
            print(json.dumps({
                "event": "cleanup_stale",
                "store": store_name,
                "deleted": result,
                "threshold_hours": STALE_PRODUCT_THRESHOLD_HOURS,
            }))
            return result
        except Exception as e:
            print(json.dumps({
                "event": "cleanup_error",
                "store": store_name,
                "error": str(e),
            }))
            return 0

    async def close(self):
        """Close all scrapers."""
        for scraper in self.scrapers.values():
            await scraper.close()
