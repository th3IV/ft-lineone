import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scrapers.collectors.falabella_scraper import FalabellaScraper
from scrapers.collectors.ripley_scraper import RipleyScraper
from scrapers.collectors.paris_scraper import ParisScraper
from scrapers.collectors.maui_scraper import MauiScraper
from scrapers.collectors.zara_scraper import ZaraScraper

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


class ScrapeRequest(BaseModel):
    store: str
    category: str = "ropa"
    max_items: int = 20


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ft-lineone-scrapers"}


@app.post("/scrape")
async def scrape(req: ScrapeRequest):
    store = req.store.lower()
    if store not in SCRAPER_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown store: {store}. Available: {list(SCRAPER_REGISTRY.keys())}")
    scraper_cls = SCRAPER_REGISTRY[store]
    scraper = scraper_cls()
    try:
        products = scraper.scrape(category=req.category, max_items=req.max_items)
        return {
            "success": True,
            "store": store,
            "category": req.category,
            "count": len(products),
            "products": [p.to_dict() for p in products],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products")
async def get_products(store: str | None = None):
    if store and store.lower() not in SCRAPER_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown store: {store}")
    return {"products": []}


def main():
    uvicorn.run("__main__:app", host="0.0.0.0", port=8001, reload=False)


if __name__ == "__main__":
    main()
