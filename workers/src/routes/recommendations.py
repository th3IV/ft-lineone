"""Recommendation routes."""

from fastapi import APIRouter, HTTPException, Request
from typing import Optional

from models.product import ProductResponse
from services.llm import LLMService

router = APIRouter()


def get_db(request: Request):
    """Get database service from request state."""
    return request.app.state.db


@router.get("")
async def get_recommendations(
    request: Request,
    query: Optional[str] = None,
):
    """Get personalized product recommendations."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    db = get_db(request)
    llm_service = LLMService(request.app.state.env)

    # Get user preferences (simplified - in real app, fetch from DB)
    user_preferences = {
        "gender": None,
        "clothing_type": [],
        "budget": None,
    }

    # Get available products
    products, _ = await db.get_products({}, page=1, limit=50)

    # Convert products to dicts for LLM
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

    # Get recommendations from LLM
    recommendations = await llm_service.get_recommendations(
        user_preferences=user_preferences,
        available_products=products_dict,
        query=query,
    )

    # Fetch full product details for recommended products
    recommended_products = []
    for rec in recommendations:
        product = await db.get_product(rec["product_id"])
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
                    sizes=product.sizes or [],
                    colors=product.colors or [],
                    availability=product.availability,
                    created_at=product.created_at,
                )
            )

    return {
        "user_id": user_id,
        "recommendations": recommended_products,
        "count": len(recommended_products),
    }


@router.post("/chat")
async def style_chat(
    request: Request,
    product_id: Optional[str] = None,
    question: str = "",
):
    """Get style advice via chat."""
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    db = get_db(request)
    llm_service = LLMService(request.app.state.env)

    product_name = "unknown product"
    product_category = "unknown"

    if product_id:
        product = await db.get_product(product_id)
        if product:
            product_name = product.name
            product_category = product.category

    advice = await llm_service.get_style_advice(
        product_name=product_name,
        product_category=product_category,
        user_question=question,
    )

    return {
        "advice": advice,
        "product_id": product_id,
    }
