"""Scraper Durable Object — consumes scraper jobs from Cloudflare Queues."""

import json
import asyncio
from datetime import datetime, timezone

from workers import DurableObject, Response
from services.database import DatabaseService
from services.config import MIN_PRODUCTS_SCRAPED_BEFORE_CLEANUP, MIN_SCRAPE_COVERAGE_RATIO, STALE_PRODUCT_THRESHOLD_HOURS
from scrapers.scheduler import ScraperRunner


RATE_LIMITS = {
    "maui": 2.0,
    "zara": 3.0,
    "falabella": 1.5,
    "hm": 1.5,
    "fashionpark": 1.0,
    "paris": 2.0,
    "ripley": 3.0,
}

RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 2.0

STORE_CATEGORIES = {
    "maui": {
        "type": "category",
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
        "type": "category",
        "categories": ["mujer", "hombre"],
    },
    "falabella": {
        "type": "search",
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
        "type": "search",
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
        "type": "search",
        "queries": [
            "polera mujer",
            "polera hombre",
            "jean mujer",
            "jean hombre",
            "vestido mujer",
            "chaqueta mujer",
        ],
    },
    "paris": {
        "type": "search",
        "queries": [
            "polera mujer",
            "polera hombre",
            "jean mujer",
            "jean hombre",
            "vestido mujer",
            "chaqueta mujer",
        ],
    },
    "ripley": {
        "type": "search",
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


class ScraperWorker:
    """Durable Object that processes scraper jobs from the queue."""

    def __init__(self, env, state):
        self.env = env
        self.state = state
        self.runner = ScraperRunner(env)

    async def fetch(self, request):
        """Handle incoming queue messages via HTTP (Queue calls DO via HTTP)."""
        if request.method != "POST":
            return Response("Method not allowed", status=405)

        try:
            body = await request.json()
            messages = body.get("messages", [])
            results = []

            for msg in messages:
                result = await self._process_message(msg)
                results.append(result)

            return Response(json.dumps({"processed": len(results), "results": results}), status=200)
        except Exception as e:
            return Response(json.dumps({"error": str(e)}), status=500)

    async def _process_message(self, message):
        """Process a single scraper job message."""
        payload = message.get("body", {})
        store = payload.get("store")
        max_products = payload.get("max_products", 30)

        if not store or store not in STORE_CATEGORIES:
            return {"store": store, "status": "error", "error": f"Unknown store: {store}"}

        print(json.dumps({"event": "scraper_job_start", "store": store, "max_products": max_products}))

        try:
            result = await self.runner.run_single_store(store, max_products)
            return {"store": store, "status": "completed", "result": result}
        except Exception as e:
            print(json.dumps({"event": "scraper_job_error", "store": store, "error": str(e)}))
            return {"store": store, "status": "failed", "error": str(e)}


class ScraperWorkerEntrypoint(DurableObject):
    """Cloudflare Workers Python entry point for the ScraperWorker DO."""

    def __init__(self, ctx, env):
        super().__init__(ctx, env)
        self.worker = ScraperWorker(env, ctx)

    async def fetch(self, request):
        return await self.worker.fetch(request)