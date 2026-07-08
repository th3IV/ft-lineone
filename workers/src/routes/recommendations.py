"""Recommendation routes."""

from datetime import datetime
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

    # Check LLM usage limit
    user_obj = await db.get_user_by_id(user.user_id)
    is_premium = getattr(user_obj, 'is_premium', False) or getattr(user_obj, 'plan_type', 'free') == 'premium'

    if not is_premium:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        usage = await db.get_user_usage(user.user_id, today)
        if usage.get("llm_count", 0) >= 10:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "usage_limit_exceeded",
                    "message": "Límite diario de recomendaciones alcanzado (10/10)",
                    "current": usage["llm_count"],
                    "limit": 10,
                    "upgrade_url": "/payment/upgrade",
                },
            )
        await db.increment_usage(user.user_id, "llm", today)

    # Read actual user preferences from DB
    user_obj = await db.get_user_by_id(user.user_id)
    user_preferences = {
        "gender": None,
        "clothing_type": [],
        "budget": None,
        "colors": [],
        "occasions": [],
        "sizes": {},
        "body_measurements": {},
        "age": None,
    }
    if user_obj:
        if user_obj.preferences:
            user_preferences["clothing_type"] = user_obj.preferences.get("styles", [])
            user_preferences["colors"] = user_obj.preferences.get("colors", [])
            user_preferences["occasions"] = user_obj.preferences.get("occasions", [])
            user_preferences["sizes"] = user_obj.preferences.get("sizes", {})
        if user_obj.body_measurements:
            user_preferences["gender"] = user_obj.body_measurements.get("gender")
            user_preferences["body_measurements"] = user_obj.body_measurements
        if user_obj.age:
            user_preferences["age"] = user_obj.age

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
        user_id=user.user_id,
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

    # Check LLM usage limit for authenticated users
    if user:
        user_obj = await db.get_user_by_id(user.user_id)
        is_premium = getattr(user_obj, 'is_premium', False) or getattr(user_obj, 'plan_type', 'free') == 'premium'

        if not is_premium:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            usage = await db.get_user_usage(user.user_id, today)
            if usage.get("llm_count", 0) >= 10:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "usage_limit_exceeded",
                        "message": "Límite diario de recomendaciones alcanzado (10/10)",
                        "current": usage["llm_count"],
                        "limit": 10,
                        "upgrade_url": "/payment/upgrade",
                    },
                )
            await db.increment_usage(user.user_id, "llm", today)
    else:
        user_obj = None

    product_name = "unknown product"
    product_category = "unknown"

    if body.product_id:
        product = await db.get_product(body.product_id)
        if product:
            product_name = product.name
            product_category = product.category

    # Build user context from preferences if authenticated
    user_context = ""
    if user and user_obj:
        if user_obj:
            parts = []
            if user_obj.preferences:
                styles = user_obj.preferences.get("styles", [])
                colors = user_obj.preferences.get("colors", [])
                occasions = user_obj.preferences.get("occasions", [])
                sizes = user_obj.preferences.get("sizes", {})
                if styles:
                    parts.append(f"estilos={styles}")
                if colors:
                    parts.append(f"colores favoritos={colors}")
                if occasions:
                    parts.append(f"ocasiones={occasions}")
                if sizes:
                    parts.append(f"tallas preferidas={sizes}")
            if user_obj.body_measurements:
                m = user_obj.body_measurements
                gender = m.get("gender", "")
                height = m.get("height", "")
                weight = m.get("weight", "")
                chest = m.get("chest", "")
                waist = m.get("waist", "")
                hips = m.get("hips", "")
                body_shape = m.get("bodyShape", "")
                if gender:
                    parts.append(f"genero={gender}")
                if height:
                    parts.append(f"altura={height}cm")
                if weight:
                    parts.append(f"peso={weight}kg")
                if chest:
                    parts.append(f"busto={chest}cm")
                if waist:
                    parts.append(f"cintura={waist}cm")
                if hips:
                    parts.append(f"caderas={hips}cm")
                if body_shape:
                    parts.append(f"forma del cuerpo={body_shape}")
            if user_obj.age:
                parts.append(f"edad={user_obj.age}")
            if parts:
                user_context = f"\nDatos completos del usuario: {', '.join(parts)}"

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

    product_lookup = {p.id: p for p in products}

    advice, product_recs = await llm_service.get_style_advice_with_products(
        product_name=product_name,
        product_category=product_category,
        user_question=body.question,
        user_context=user_context,
        available_products=products_dict,
        user_id=user.user_id if user else None,
    )

    recommended_products = []
    seen_ids = set()
    for rec in product_recs:
        pid = rec.get("product_id")
        if not pid or pid in seen_ids:
            continue
        product = product_lookup.get(pid)
        if product:
            seen_ids.add(pid)
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

    return {"advice": advice, "products": recommended_products, "product_id": body.product_id}
