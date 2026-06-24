import asyncio
import logging

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scrapers.scrapers.falabella_scraper import FalabellaScraper
from scrapers.scrapers.ripley_scraper import RipleyScraper
from scrapers.scrapers.paris_scraper import ParisScraper
from scrapers.scrapers.maui_scraper import MauiScraper
from scrapers.scrapers.zara_scraper import ZaraScraper
from scrapers.pipeline.publisher import Publisher

logger = logging.getLogger(__name__)

app = FastAPI(title="FT LineOne Scrapers", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCRAPER_REGISTRY: dict[str, type] = {
    "falabella": FalabellaScraper,
    "ripley": RipleyScraper,
    "paris": ParisScraper,
    "maui": MauiScraper,
    "zara": ZaraScraper,
}

STORES = list(SCRAPER_REGISTRY.keys())

scheduler = BackgroundScheduler()


def scrape_store_sync(store: str, category: str = "ropa", max_items: int = 20):
    scraper_cls = SCRAPER_REGISTRY[store]
    scraper = scraper_cls()
    products = scraper.scrape(category=category, max_items=max_items)
    publisher = Publisher()
    results = publisher.publish_batch(products)
    publisher.close()
    saved = sum(1 for r in results if "product_id" in r)
    failed = sum(1 for r in results if "error" in r)
    logger.info("Scraped %s: %d saved, %d failed", store, saved, failed)
    return {"store": store, "total": len(products), "saved": saved, "failed": failed}


def scrape_all_stores():
    logger.info("Starting scheduled scrape of all stores")
    for store in STORES:
        try:
            scrape_store_sync(store)
        except Exception as e:
            logger.error("Failed to scrape %s: %s", store, e)
    logger.info("Scheduled scrape completed")


class ScrapeRequest(BaseModel):
    store: str
    category: str = "ropa"
    max_items: int = 20


@app.on_event("startup")
async def startup():
    scheduler.add_job(
        scrape_all_stores,
        trigger="interval",
        hours=6,
        id="scrape_all_stores",
        name="Scrape all stores every 6 hours",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Started periodic scrape scheduler (every 6 hours)")
    scrape_all_stores()


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown(wait=False)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ft-lineone-scrapers"}


@app.get("/scrape")
@app.post("/scrape")
async def scrape(
    store: str = "falabella",
    category: str = "ropa",
    max_items: int = 20,
    req: ScrapeRequest | None = None,
):
    if req:
        store, category, max_items = req.store.lower(), req.category, req.max_items
    else:
        store = store.lower()
    if store not in SCRAPER_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown store: {store}. Available: {list(SCRAPER_REGISTRY.keys())}")
    scraper_cls = SCRAPER_REGISTRY[store]
    scraper = scraper_cls()
    try:
        products = await asyncio.to_thread(scraper.scrape, category, max_items)
        return {
            "success": True,
            "store": store,
            "category": category,
            "count": len(products),
            "products": [p.to_dict() for p in products],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scrape-and-save")
@app.post("/scrape-and-save")
async def scrape_and_save(
    store: str = "falabella",
    category: str = "ropa",
    max_items: int = 20,
    req: ScrapeRequest | None = None,
):
    if req:
        store, category, max_items = req.store.lower(), req.category, req.max_items
    else:
        store = store.lower()
    if store not in SCRAPER_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown store: {store}. Available: {list(SCRAPER_REGISTRY.keys())}")
    try:
        result = await asyncio.to_thread(scrape_store_sync, store, category, max_items)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    uvicorn.run("scrapers.__main__:app", host="0.0.0.0", port=8001, reload=False)


if __name__ == "__main__":
    main()
