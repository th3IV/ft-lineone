"""Scraper routes for ingesting products."""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from ..scrapers.falabella import FalabellaScraper
from ..scrapers.hites import HitesScraper
from ..scrapers.fashionpark import FashionParkScraper
from ..scrapers.hm import HMScraper
from models.product import ProductCreate
from middleware.security import require_auth

router = APIRouter()


def get_db(request: Request):
    """Get database service from request state."""
    return request.app.state.db


class ScraperIngestRequest(BaseModel):
    external_id: str
    store: str
    name: str
    description: str = ""
    price: float
    currency: str = "CLP"
    original_url: str = ""
    image_urls: list[str] = []
    category: str = ""
    sizes: list[str] = []
    colors: list[str] = []
    availability: bool = True


@router.post("/ingest")
async def ingest_product(product_data: ScraperIngestRequest, request: Request):
    """Ingest a product from a scraper."""
    db = get_db(request)

    existing_products, _ = await db.get_products(
        {"store": product_data.store}, page=1, limit=1000,
    )

    for p in existing_products:
        if p.external_id == product_data.external_id:
            return {
                "status": "skipped",
                "message": f"Product {product_data.external_id} already exists",
                "product_id": p.id,
            }

    product = await db.create_product({
        "external_id": product_data.external_id,
        "name": product_data.name,
        "store": product_data.store,
        "price": product_data.price,
        "currency": product_data.currency,
        "category": product_data.category,
        "description": product_data.description,
        "original_url": product_data.original_url,
        "image_url": product_data.image_urls[0] if product_data.image_urls else None,
        "image_urls": product_data.image_urls,
        "sizes": product_data.sizes,
        "colors": product_data.colors,
        "availability": product_data.availability,
    })

    return {
        "status": "created",
        "product_id": product.id,
        "message": f"Product {product_data.external_id} ingested successfully",
    }


@router.post("/ingest/batch")
async def ingest_batch(products: list[ScraperIngestRequest], request: Request):
    """Ingest multiple products from scrapers."""
    db = get_db(request)
    results = []

    for product_data in products:
        try:
            result = await ingest_product(product_data, request)
            results.append(result)
        except Exception as e:
            results.append({
                "status": "error",
                "external_id": product_data.external_id,
                "error": str(e),
            })

    return {
        "total": len(products),
        "created": sum(1 for r in results if r["status"] == "created"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
        "errors": sum(1 for r in results if r["status"] == "error"),
        "results": results,
    }


@router.get("/health")
async def health_check():
    """Health check for scraper service."""
    return {"status": "healthy", "service": "scrapers"}


@router.post("/run")
async def run_scrapers(request: Request, user: dict = Depends(require_auth)):
    """Manually trigger scrapers for testing. Returns detailed results."""
    from scrapers.scheduler import ScraperRunner

    runner = ScraperRunner(request.app.state.env, max_products=20)
    try:
        results = await runner.run_all_scrapers()
        return {"status": "completed", "results": results}
    except Exception as e:
        return {"status": "error", "error": str(e), "type": type(e).__name__}
    finally:
        await runner.close()


@router.post("/run/{store}")
async def run_single_scraper(store: str, request: Request, user: dict = Depends(require_auth)):
    """Manually trigger a single store scraper for testing."""
    from scrapers.scheduler import ScraperRunner
    from scrapers.zara import ZaraScraper
    from scrapers.paris import ParisScraper
    from scrapers.maui import MauiScraper

    scraper_map = {
        "zara": ZaraScraper,
        "paris": ParisScraper,
        "maui": MauiScraper,
        "falabella": FalabellaScraper,
        "hites": HitesScraper,
        "fashionpark": FashionParkScraper,
        "hm": HMScraper,
    }

    if store not in scraper_map:
        raise HTTPException(status_code=400, detail=f"Unknown store: {store}. Valid: {list(scraper_map.keys())}")

    runner = ScraperRunner(request.app.state.env, max_products=5)
    try:
        scraper = scraper_map[store]()
        result = await runner._run_scraper(store, scraper)
        await scraper.close()
        return {"store": store, "result": result}
    except Exception as e:
        return {"store": store, "error": str(e), "type": type(e).__name__}


@router.get("/debug/{store}")
async def debug_scraper(store: str):
    """Debug endpoint: shows what a store actually returns."""
    import httpx

    debug_info = {"store": store, "tests": []}

    if store == "paris":
        client = httpx.AsyncClient(timeout=15.0, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "es-CL,es;q=0.9",
        })
        try:
            # Test 1: Constructor.io JS bundle
            r1 = await client.get("https://cnstrc.com/js/cust/cencosud_0BmS-e.js")
            import re
            match = re.search(r"key[=:]\s*['\"]?([a-zA-Z0-9_-]+)['\"]?", r1.text) if r1.status_code == 200 else None
            debug_info["tests"].append({
                "test": "cnstrc_js",
                "status": r1.status_code,
                "content_length": len(r1.text),
                "key_found": match.group(1) if match else None,
            })

            # Test 2: Constructor.io search
            if match:
                key = match.group(1)
                r2 = await client.get("https://ac.cnstrc.com/search", params={
                    "key": key, "i": "polera mujer", "num_results_per_page": 5, "section": "Products",
                })
                data = r2.json() if r2.status_code == 200 else {}
                results = data.get("response", {}).get("results", [])
                debug_info["tests"].append({
                    "test": "cnstrc_search",
                    "status": r2.status_code,
                    "results_count": len(results),
                    "first_result": results[0] if results else None,
                })

            # Test 3: Direct HTML
            r3 = await client.get("https://www.paris.cl/search", params={"q": "polera mujer"})
            debug_info["tests"].append({
                "test": "html_search",
                "status": r3.status_code,
                "content_length": len(r3.text),
                "has_next_data": "__NEXT_DATA__" in r3.text,
                "snippet": r3.text[:500] if r3.status_code == 200 else f"Error {r3.status_code}",
            })
        except Exception as e:
            debug_info["error"] = str(e)
        finally:
            await client.aclose()

    elif store == "zara":
        client = httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "es-CL,es;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.zara.com/cl/es/",
        })
        try:
            # Test 1: Categories API
            r1 = await client.get("https://www.zara.com/cl/es/categories?ajax=true")
            cats = r1.json() if r1.status_code == 200 else []
            debug_info["tests"].append({
                "test": "categories_api",
                "status": r1.status_code,
                "categories_count": len(cats),
            })

            # Test 2: Products for CAMISETAS mujer (2509505)
            r2 = await client.get("https://www.zara.com/cl/es/category/2509505/products?ajax=true")
            data = r2.json() if r2.status_code == 200 else {}
            groups = data.get("productGroups", [])
            products_found = []
            for g in groups:
                for el in g.get("elements", []):
                    for comp in el.get("commercialComponents", []):
                        if comp.get("kind") not in ("Bundle", "Marketing", "Editorial"):
                            products_found.append({
                                "name": comp.get("name"),
                                "id": comp.get("id"),
                                "price": comp.get("price"),
                                "kind": comp.get("kind"),
                                "availability": comp.get("availability"),
                            })
            debug_info["tests"].append({
                "test": "products_api",
                "status": r2.status_code,
                "groups_count": len(groups),
                "products_found": len(products_found),
                "first_3": products_found[:3],
            })
        except Exception as e:
            debug_info["error"] = str(e)
        finally:
            await client.aclose()

    elif store == "maui":
        client = httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "es-CL,es;q=0.9",
        })
        try:
            r1 = await client.get("https://mauiandsons.cl/hombre/vestuario/poleras.html")
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r1.text, "html.parser") if r1.status_code == 200 else None
            products = soup.select(".product-item, .product-item-info, [data-product-id]") if soup else []

            debug_info["tests"].append({
                "test": "maui_poleras",
                "status": r1.status_code,
                "content_length": len(r1.text),
                "product_elements": len(products),
                "snippet": r1.text[:500] if r1.status_code == 200 else f"Error {r1.status_code}",
            })
        except Exception as e:
            debug_info["error"] = str(e)
        finally:
            await client.aclose()

    return debug_info
