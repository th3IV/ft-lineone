"""Scraper routes for ingesting products."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from models.product import ProductCreate

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

    # Check if product already exists by external_id and store
    existing_products, _ = await db.get_products(
        {"store": product_data.store},
        page=1,
        limit=1000,
    )

    # Check for duplicate
    for p in existing_products:
        if p.external_id == product_data.external_id:
            return {
                "status": "skipped",
                "message": f"Product {product_data.external_id} already exists",
                "product_id": p.id,
            }

    # Create new product
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
