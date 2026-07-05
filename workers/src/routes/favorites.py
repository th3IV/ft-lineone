"""Favorites routes — CRUD for user product favorites."""

from fastapi import APIRouter, HTTPException, Request, Depends

from middleware.security import require_auth

router = APIRouter()


def get_db(request: Request):
    return request.app.state.db


@router.get("")
async def get_favorites(
    request: Request,
    page: int = 1,
    limit: int = 20,
    user: dict = Depends(require_auth),
):
    """Get current user's favorite products."""
    db = get_db(request)
    products, total = await db.get_favorites(user.user_id, page=page, limit=limit)
    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "store": p.store,
                "price": p.price,
                "currency": p.currency,
                "category": p.category,
                "image_url": p.image_url,
                "image_urls": p.image_urls or [],
                "sizes": p.sizes or [],
                "colors": p.colors or [],
                "availability": p.availability,
                "original_url": p.original_url,
                "created_at": p.created_at,
            }
            for p in products
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/check/{product_id}")
async def check_favorite(
    product_id: str,
    request: Request,
    user: dict = Depends(require_auth),
):
    """Check if a product is favorited by the current user."""
    db = get_db(request)
    is_fav = await db.is_favorite(user.user_id, product_id)
    return {"is_favorite": is_fav}


@router.post("/{product_id}")
async def add_favorite(
    product_id: str,
    request: Request,
    user: dict = Depends(require_auth),
):
    """Add a product to favorites."""
    db = get_db(request)
    product = await db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    already = await db.is_favorite(user.user_id, product_id)
    if already:
        return {"status": "already_favorited", "is_favorite": True}
    await db.add_favorite(user.user_id, product_id)
    return {"status": "added", "is_favorite": True}


@router.delete("/{product_id}")
async def remove_favorite(
    product_id: str,
    request: Request,
    user: dict = Depends(require_auth),
):
    """Remove a product from favorites."""
    db = get_db(request)
    await db.remove_favorite(user.user_id, product_id)
    return {"status": "removed", "is_favorite": False}
