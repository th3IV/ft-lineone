"""Product routes."""

import math
from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional

from models.product import ProductResponse, ProductListResponse, ProductCreate

router = APIRouter()


def get_db(request: Request):
    """Get database service from request state."""
    return request.app.state.db


@router.get("", response_model=ProductListResponse)
async def list_products(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    store: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    q: Optional[str] = None,
    gender: Optional[str] = None,
    clothing_type: Optional[str] = None,
    size: Optional[str] = None,
    color: Optional[str] = None,
):
    """List products with filters and pagination."""
    db = get_db(request)

    filters = {}
    if store:
        filters["store"] = store
    if category:
        filters["category"] = category
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price
    if q:
        filters["query"] = q

    products, total = await db.get_products(filters, page, limit)
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    return ProductListResponse(
        products=[
            ProductResponse(
                id=p.id,
                name=p.name,
                store=p.store,
                price=p.price,
                currency=p.currency,
                category=p.category,
                description=p.description,
                original_url=p.original_url,
                image_url=p.image_url,
                sizes=p.sizes or [],
                colors=p.colors or [],
                availability=p.availability,
                created_at=p.created_at,
            )
            for p in products
        ],
        total=total,
        page=page,
        per_page=limit,
        total_pages=total_pages,
    )


@router.get("/search", response_model=ProductListResponse)
async def search_products(
    request: Request,
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Search products by query."""
    db = get_db(request)

    products, total = await db.get_products({"query": q}, page, limit)
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    return ProductListResponse(
        products=[
            ProductResponse(
                id=p.id,
                name=p.name,
                store=p.store,
                price=p.price,
                currency=p.currency,
                category=p.category,
                description=p.description,
                image_url=p.image_url,
                sizes=p.sizes or [],
                colors=p.colors or [],
                availability=p.availability,
                created_at=p.created_at,
            )
            for p in products
        ],
        total=total,
        page=page,
        per_page=limit,
        total_pages=total_pages,
    )


@router.get("/store/{store}", response_model=ProductListResponse)
async def list_products_by_store(
    request: Request,
    store: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """List products filtered by store."""
    db = get_db(request)

    products, total = await db.get_products({"store": store}, page, limit)
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    return ProductListResponse(
        products=[
            ProductResponse(
                id=p.id,
                name=p.name,
                store=p.store,
                price=p.price,
                currency=p.currency,
                category=p.category,
                description=p.description,
                image_url=p.image_url,
                sizes=p.sizes or [],
                colors=p.colors or [],
                availability=p.availability,
                created_at=p.created_at,
            )
            for p in products
        ],
        total=total,
        page=page,
        per_page=limit,
        total_pages=total_pages,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(request: Request, product_id: str):
    """Get a product by ID."""
    db = get_db(request)

    product = await db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductResponse(
        id=product.id,
        name=product.name,
        store=product.store,
        price=product.price,
        currency=product.currency,
        category=product.category,
        description=product.description,
        original_url=product.original_url,
        image_url=product.image_url,
        sizes=product.sizes or [],
        colors=product.colors or [],
        availability=product.availability,
        created_at=product.created_at,
    )


@router.post("", response_model=ProductResponse)
async def create_product(product_data: ProductCreate, request: Request):
    """Create a new product (admin only)."""
    db = get_db(request)

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

    return ProductResponse(
        id=product.id,
        name=product.name,
        store=product.store,
        price=product.price,
        currency=product.currency,
        category=product.category,
        description=product.description,
        original_url=product.original_url,
        image_url=product.image_url,
        sizes=product.sizes or [],
        colors=product.colors or [],
        availability=product.availability,
        created_at=product.created_at,
    )
