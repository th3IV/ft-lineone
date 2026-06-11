from math import ceil

from fastapi import APIRouter, HTTPException, Query

from app.application.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


def get_product_service():
    return ProductService()


@router.get("")
async def list_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    svc = get_product_service()
    products, total = await svc.get_catalog(page=page, per_page=per_page)
    return {
        "products": [p.model_dump() for p in products],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": ceil(total / per_page),
    }


@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    svc = get_product_service()
    products, total = await svc.search(query=q, page=page, per_page=per_page)
    return {
        "products": [p.model_dump() for p in products],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": ceil(total / per_page),
    }


@router.get("/store/{store}")
async def products_by_store(
    store: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    svc = get_product_service()
    products, total = await svc.get_by_store(
        store=store, page=page, per_page=per_page
    )
    return {
        "store": store,
        "products": [p.model_dump() for p in products],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": ceil(total / per_page),
    }


@router.get("/{product_id}")
async def get_product(product_id: str):
    svc = get_product_service()
    product = await svc.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.model_dump()
