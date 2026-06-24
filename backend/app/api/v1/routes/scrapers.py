from fastapi import APIRouter, HTTPException

from app.application.services.product_service import ProductService
from app.domain.models.product import Product

router = APIRouter(prefix="/scrapers", tags=["scrapers"])


def get_product_service():
    return ProductService()


@router.post("/ingest")
async def ingest_product(payload: dict):
    svc = get_product_service()
    try:
        product = Product(
            external_id=payload.get("external_id", ""),
            store=payload.get("store", ""),
            name=payload.get("name", ""),
            description=payload.get("description", ""),
            price=float(payload.get("price", 0)),
            currency=payload.get("currency", "USD"),
            image_url=(payload.get("image_urls") or [None])[0] or "",
            category=payload.get("category", ""),
            sizes=payload.get("sizes", []),
            colors=payload.get("colors", []),
        )
        saved = await svc.upsert_product(product)
        return {"success": True, "product_id": saved.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
