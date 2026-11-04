from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.application.services.product_service import ProductService
from app.domain.models.product import Product

router = APIRouter(prefix="/scrapers", tags=["scrapers"])


class IngestProductRequest(BaseModel):
    external_id: str
    store: str
    name: str
    description: str = ""
    price: float
    currency: str = "USD"
    original_url: str = ""
    image_urls: list[str] = []
    category: str = ""
    sizes: list[str] = []
    colors: list[str] = []
    availability: bool = True


class IngestBatchRequest(BaseModel):
    products: list[IngestProductRequest]


def get_product_service():
    return ProductService()


def _to_domain(req: IngestProductRequest) -> Product:
    return Product(
        external_id=req.external_id,
        store=req.store,
        name=req.name,
        description=req.description,
        price=req.price,
        currency=req.currency or "CLP",
        image_url=req.image_urls[0] if req.image_urls else "",
        category=req.category,
        sizes=req.sizes,
        colors=req.colors,
        scraped_at=datetime.now(timezone.utc),
    )


@router.post("/ingest")
async def ingest_product(body: IngestProductRequest):
    svc = get_product_service()
    try:
        product = await svc._product_repo.create(_to_domain(body))
        return {"status": "ok", "product_id": product.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/batch")
async def ingest_batch(body: IngestBatchRequest):
    svc = get_product_service()
    results = []
    for req in body.products:
        try:
            product = await svc._product_repo.create(_to_domain(req))
            results.append({"external_id": req.external_id, "status": "ok", "product_id": product.id})
        except Exception as e:
            results.append({"external_id": req.external_id, "status": "error", "detail": str(e)})
    return {"results": results}
