"""Recommendation routes."""

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional
from pydantic import BaseModel

from models.product import ProductResponse
from services.llm import LLMService
from middleware.security import require_auth, optional_auth

router = APIRouter()


def get_db(request: Request):
    """Get database service from request state."""
    return request.app.state.db


class ChatRequest(BaseModel):
    question: str
    product_id: Optional[str] = None


@router.get("")
async def get_recommendations(
    request: Request,
    query: Optional[str] = None,
    user: dict = Depends(require_auth),
):
    """Get personalized product recommendations."""
    db = get_db(request)
    llm_service = LLMService(request.app.state.env)

    # Read actual user preferences from DB
    user_obj = await db.get_user_by_id(user.user_id)
    user_preferences = {
        "gender": None,
        "clothing_type": [],
        "budget": None,
    }
    if user_obj:
        if user_obj.preferences:
            user_preferences["clothing_type"] = user_obj.preferences
        if user_obj.body_measurements:
            user_preferences["gender"] = user_obj.body_measurements.get("gender")

    products, _ = await db.get_products({}, page=1, limit=50)

    products_dict = [
        {
            "id": p.id,
            "name": p.name,
            "store": p.store,
            "price": p.price,
            "category": p.category,
            "colors": p.colors or [],
        }
        for p in products
    ]

    recommendations = await llm_service.get_recommendations(
        user_preferences=user_preferences,
        available_products=products_dict,
        query=query,
    )

    # Build lookup dict to avoid N+1 queries
    product_lookup = {p.id: p for p in products}

    recommended_products = []
    for rec in recommendations:
        product = product_lookup.get(rec["product_id"])
        if product:
            recommended_products.append(
                ProductResponse(
                    id=product.id,
                    name=product.name,
                    store=product.store,
                    price=product.price,
                    currency=product.currency,
                    category=product.category,
                    description=product.description,
                    image_url=product.image_url,
                    image_urls=product.image_urls or [],
                    sizes=product.sizes or [],
                    colors=product.colors or [],
                    availability=product.availability,
                    created_at=product.created_at,
                )
            )

    return {
        "user_id": user.user_id,
        "recommendations": recommended_products,
        "count": len(recommended_products),
    }


@router.post("/chat")
async def style_chat(
    request: Request,
    body: ChatRequest,
    user: dict = Depends(optional_auth),
):
    """Get style advice via chat."""
    if not body.question:
        raise HTTPException(status_code=400, detail="Question is required")

    db = get_db(request)
    llm_service = LLMService(request.app.state.env)

    product_name = "unknown product"
    product_category = "unknown"

    if body.product_id:
        product = await db.get_product(body.product_id)
        if product:
            product_name = product.name
            product_category = product.category

    advice = await llm_service.get_style_advice(
        product_name=product_name,
        product_category=product_category,
        user_question=body.question,
    )

    return {"advice": advice, "product_id": body.product_id}
