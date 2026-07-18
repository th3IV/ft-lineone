"""Scraper routes for ingesting products."""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from models.product import ProductCreate
from middleware.security import require_auth, require_admin

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
async def ingest_product(product_data: ScraperIngestRequest, request: Request, user: dict = Depends(require_admin)):
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
async def ingest_batch(products: list[ScraperIngestRequest], request: Request, user: dict = Depends(require_admin)):
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
async def run_scrapers(request: Request, user: dict = Depends(require_admin)):
    """Manually trigger scrapers for testing. Returns detailed results."""
    from scrapers.scheduler import ScraperRunner

    runner = ScraperRunner(request.app.state.env, max_products=20)
    try:
        results = await runner.run_all_scrapers()
        return {"status": "completed", "results": results}
    except Exception as e:
        return {"status": "error", "error": "Scraper execution failed"}
    finally:
        await runner.close()


@router.post("/trigger")
async def trigger_scrapers(request: Request, user: dict = Depends(require_admin)):
    """Trigger all scrapers. Requires authentication."""
    from scrapers.scheduler import ScraperRunner

    runner = ScraperRunner(request.app.state.env, max_products=10)
    try:
        results = await runner.run_all_scrapers()
        return {"status": "completed", "results": results}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await runner.close()


@router.post("/reset/{store}")
async def reset_store(store: str, request: Request, user: dict = Depends(require_admin)):
    """EMERGENCY ONLY: Delete all products from a store and re-scrape.

    Requires authentication. This endpoint is for emergency use only when data
    is severely corrupted and the automatic cleanup in the cron cannot fix it.
    Normal data cleanup happens automatically every 2 minutes via cron.
    """
    from scrapers.scheduler import ScraperRunner

    db = request.app.state.db

    # Delete all products from the store
    try:
        deleted_count = await db.delete_products_by_store(store)
    except Exception as e:
        return {"status": "error", "error": f"Failed to delete: {str(e)}"}

    # Re-scrape the store
    runner = ScraperRunner(request.app.state.env, max_products=20)
    try:
        if store not in runner.scrapers:
            return {"status": "error", "error": f"Unknown store: {store}"}

        result = await runner._run_scraper(store, runner.scrapers[store])
        return {
            "status": "completed",
            "store": store,
            "deleted_count": deleted_count,
            "scrape_result": result,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await runner.close()


@router.post("/run/{store}")
async def run_single_scraper(store: str, request: Request, user: dict = Depends(require_admin)):
    """Manually trigger a single store scraper for testing."""
    from scrapers.scheduler import ScraperRunner
    from scrapers.zara import ZaraScraper
    from scrapers.maui import MauiScraper
    from scrapers.falabella import FalabellaScraper
    from scrapers.fashionpark import FashionParkScraper
    from scrapers.hm import HMScraper

    scraper_map = {
        "zara": ZaraScraper,
        "maui": MauiScraper,
        "falabella": FalabellaScraper,
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


@router.post("/enrich-missing")
async def enrich_missing_sizes(request: Request, user: dict = Depends(require_admin)):
    """Enrich products that have empty sizes by fetching from store APIs."""
    import json as _json
    import js
    from pyodide.ffi import to_js as _to_js
    from js import Object

    def to_js(obj):
        return _to_js(obj, dict_converter=Object.fromEntries)

    db = get_db(request)
    results = {"stores": {}}

    # Fashion Park enrichment
    fp_products = await db.get_products_without_sizes("fashionpark", limit=200)
    fp_enriched = 0
    fp_errors = []
    if fp_products:
        for product in fp_products:
            try:
                handle = product.original_url.split("/products/")[-1] if product.original_url else ""
                if not handle:
                    continue
                url = f"https://fashionspark.com/products/{handle}.json"
                resp = await js.fetch(url, to_js({"method": "GET", "headers": {"Accept": "application/json"}}))
                if int(resp.status) != 200:
                    fp_errors.append(f"{handle}: HTTP {resp.status}")
                    continue
                text = await resp.text()
                data = _json.loads(text).get("product", {})
                sizes = []
                colors = []
                for opt in data.get("options", []):
                    opt_name = (opt.get("name") or "").lower()
                    if "talla" in opt_name or "size" in opt_name:
                        for v in data.get("variants", []):
                            key = f"option{opt.get('position', 1)}"
                            val = v.get(key, "")
                            if val and val not in sizes:
                                sizes.append(val)
                    elif "color" in opt_name:
                        for v in data.get("variants", []):
                            key = f"option{opt.get('position', 1)}"
                            val = v.get(key, "")
                            if val and val not in colors:
                                colors.append(val)
                if sizes:
                    await db.update_product_sizes(product.id, sizes, colors or None)
                    fp_enriched += 1
                else:
                    fp_errors.append(f"{handle}: no sizes")
            except Exception as e:
                fp_errors.append(f"{product.original_url}: {str(e)[:100]}")
                continue
    results["stores"]["fashionpark"] = {"total": len(fp_products), "enriched": fp_enriched, "errors": fp_errors[:5]}

    # Zara enrichment
    zara_products = await db.get_products_without_sizes("zara", limit=200)
    zara_enriched = 0
    zara_errors = []
    if zara_products:
        try:
            headers = to_js({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://www.zara.com/cl/es/",
            })
            cat_resp = await js.fetch("https://www.zara.com/cl/es/categories?ajax=true", to_js({"method": "GET", "headers": headers}))
            if int(cat_resp.status) == 200:
                cat_text = await cat_resp.text()
                categories = _json.loads(cat_text)
                all_sizes_by_id = {}
                for cat in categories[:10]:
                    cat_id = cat.get("id")
                    if not cat_id:
                        continue
                    try:
                        p_resp = await js.fetch(f"https://www.zara.com/cl/es/category/{cat_id}/products?ajax=true", to_js({"method": "GET", "headers": headers}))
                        if int(p_resp.status) != 200:
                            continue
                        p_text = await p_resp.text()
                        for group in _json.loads(p_text).get("productGroups", []):
                            for el in group.get("elements", []):
                                for comp in el.get("commercialComponents", []):
                                    detail = comp.get("detail", {})
                                    pid = str(comp.get("id", ""))
                                    sizes = [s.get("name", "") for s in detail.get("sizes", []) if s.get("name")]
                                    if pid and sizes:
                                        all_sizes_by_id[pid] = sizes
                    except Exception:
                        continue
                for product in zara_products:
                    sizes = all_sizes_by_id.get(product.external_id, [])
                    if sizes:
                        await db.update_product_sizes(product.id, sizes)
                        zara_enriched += 1
        except Exception as e:
            zara_errors.append(str(e)[:100])
    results["stores"]["zara"] = {"total": len(zara_products), "enriched": zara_enriched, "errors": zara_errors[:5]}

    results["summary"] = {
        "total_enriched": fp_enriched + zara_enriched,
    }
    return results


@router.get("/debug/{store}")
async def debug_scraper(store: str, request: Request, user: dict = Depends(require_admin)):
    """Debug endpoint: shows what a store actually returns. Requires auth."""
    import httpx

    debug_info = {"store": store, "tests": []}

    if store == "zara":
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


@router.get("/test-endpoints")
async def test_endpoints(request: Request, user: dict = Depends(require_admin)):
    """Test all store API endpoints and return diagnostic info. Requires auth."""
    import httpx

    results = {}

    # Test Fashion Park
    try:
        async with httpx.AsyncClient(timeout=15.0, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }) as client:
            r = await client.get("https://fashionspark.com/search/suggest.json", params={
                "q": "polera mujer",
                "resources[type]": "product",
                "resources[limit]": 5,
            })
            data = r.json() if r.status_code == 200 else {}
            products = data.get("resources", {}).get("results", {}).get("products", [])
            results["fashionpark"] = {
                "url": str(r.url),
                "status": r.status_code,
                "has_resources": "resources" in data,
                "products_count": len(products),
                "first_product": products[0] if products else None,
                "raw_keys": list(data.keys()) if isinstance(data, dict) else str(type(data)),
            }
    except Exception as e:
        results["fashionpark"] = {"error": str(e)}

    # Test H&M
    try:
        async with httpx.AsyncClient(timeout=15.0, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "es-CL,es;q=0.9",
        }) as client:
            r = await client.get("https://cl.hm.com/api/catalog_system/pub/products/search/", params={
                "q": "polera",
                "_from": 0,
                "_to": 4,
            })
            is_list = False
            products = []
            raw_type = ""
            try:
                data = r.json()
                raw_type = str(type(data))
                is_list = isinstance(data, list)
                if is_list:
                    products = data
            except:
                data = r.text[:500]
            results["hm"] = {
                "url": str(r.url),
                "status": r.status_code,
                "is_list": is_list,
                "raw_type": raw_type,
                "products_count": len(products) if is_list else 0,
                "first_product": products[0] if products else None,
                "snippet": r.text[:800] if r.status_code != 200 else (str(products[0])[:300] if products else "empty list"),
            }
    except Exception as e:
        results["hm"] = {"error": str(e)}

    return results
