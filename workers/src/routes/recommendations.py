"""Recommendation routes."""

import json
import random
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional
from pydantic import BaseModel

from models.product import ProductResponse
from services.llm import LLMService
from services.config import LLM_DAILY_LIMIT_FREE
from middleware.security import require_auth, optional_auth
from services.llm import CHAT_SYSTEM_PROMPT

router = APIRouter()


def get_db(request: Request):
    """Get database service from request state."""
    return request.app.state.db


class ChatRequest(BaseModel):
    question: str
    product_id: Optional[str] = None
    image: Optional[str] = None


@router.get("")
async def get_recommendations(
    request: Request,
    query: Optional[str] = None,
    user: dict = Depends(require_auth),
):
    """Get personalized product recommendations."""
    db = get_db(request)
    llm_service = LLMService(request.app.state.env)

    # Atomic check-and-increment LLM usage
    user_obj = await db.get_user_by_id(user.user_id)
    is_premium = getattr(user_obj, 'is_premium', False) or getattr(user_obj, 'plan_type', 'free') == 'premium'
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    effective_limit = -1 if is_premium else LLM_DAILY_LIMIT_FREE
    usage_result = await db.try_increment_usage(user.user_id, "llm", today, effective_limit)

    if not usage_result["allowed"]:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "usage_limit_exceeded",
                "message": f"Límite diario de recomendaciones alcanzado ({LLM_DAILY_LIMIT_FREE}/{LLM_DAILY_LIMIT_FREE})",
                "current": LLM_DAILY_LIMIT_FREE,
                "limit": LLM_DAILY_LIMIT_FREE,
                "upgrade_url": "/payment/upgrade",
            },
        )

    # Read actual user preferences from DB
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
    new_llm = 0
    daily_usage_response = None
    if user:
        user_obj = await db.get_user_by_id(user.user_id)
        is_premium = getattr(user_obj, 'is_premium', False) or getattr(user_obj, 'plan_type', 'free') == 'premium'

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        effective_limit = -1 if is_premium else LLM_DAILY_LIMIT_FREE
        usage_result = await db.try_increment_usage(user.user_id, "llm", today, effective_limit)

        if not usage_result["allowed"]:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "usage_limit_exceeded",
                    "message": f"Límite diario de recomendaciones alcanzado ({LLM_DAILY_LIMIT_FREE}/{LLM_DAILY_LIMIT_FREE})",
                    "current": LLM_DAILY_LIMIT_FREE,
                    "limit": LLM_DAILY_LIMIT_FREE,
                    "upgrade_url": "/payment/upgrade",
                },
            )

        new_llm = usage_result["new_count"]
        daily_usage_response = {
            "vton": 0,
            "llm": new_llm,
            "limit": effective_limit,
            "plan_type": getattr(user_obj, 'plan_type', 'free'),
        }
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

    # Build RAG query
    query = f"{product_name} {product_category} {body.question}"

    # Build filters for RAG
    rag_filters = {}
    if user_obj and user_obj.body_measurements:
        rag_filters["gender"] = user_obj.body_measurements.get("gender")
    if user_obj and user_obj.preferences:
        if user_obj.preferences.get("colors"):
            rag_filters["colors"] = user_obj.preferences["colors"]
        if user_obj.preferences.get("min_price"):
            rag_filters["min_price"] = user_obj.preferences["min_price"]
        if user_obj.preferences.get("max_price"):
            rag_filters["max_price"] = user_obj.preferences["max_price"]

    # Semantic search via RAG
    rag_results = await db.get_rag_products(query=body.question, top_k=10, filters=rag_filters)

    # Build product list for LLM
    rag_products = []
    if rag_results:
        sample_size = min(15, len(rag_results))
        sampled_products = random.sample(rag_results, sample_size) if len(rag_results) > sample_size else rag_results
        products_text = json.dumps(
            [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "store": p["store"],
                    "price": p["price"],
                    "category": p.get("category", ""),
                    "colors": p.get("colors", []),
                }
                for p in sampled_products
            ],
            ensure_ascii=False,
            indent=2,
        )
    else:
        sampled_products = products_dict[:15]
        products_text = json.dumps(
            [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "store": p["store"],
                    "price": p["price"],
                    "category": p.get("category", ""),
                    "colors": p.get("colors", []),
                }
                for p in sampled_products
            ],
            ensure_ascii=False,
            indent=2,
        )

    prompt_parts = [
        f"Producto: {product_name} (categoría: {product_category})",
        f"Pregunta del usuario: {body.question}",
    ]
    if user_context:
        prompt_parts.append(user_context)

    if rag_results:
        prompt_parts.append(f"\nProductos disponibles (SOLO puedes recomendar de esta lista):\n{products_text}")

    prompt_parts.append(
        "\n\nResponde directamente a la pregunta del usuario. "
        "SOLO si el usuario pide recomendaciones explícitamente, menciona productos usando "
        "[**NOMBRE**](/product/ID) con el id exacto de la lista. "
        "Personaliza según los datos del usuario si los tienes. "
        "Responde SOLO texto natural, sin JSON ni formato especial."
    )

    model = "@cf/meta/llama-4-scout-17b-16e-instruct"
    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(prompt_parts)},
    ]

    if body.image:
        clean_base64 = body.image.split(",")[-1] if "," in body.image else body.image
        model = "@cf/meta/llama-4-scout-17b-16e-instruct"
        messages = [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "\n".join(prompt_parts)},
                    {"type": "image_base64", "image_base64": clean_base64}
                ]
            }
        ]

    print(json.dumps({
        "event": "llm_request",
        "method": "style_chat",
        "model": model,
        "prompt_length": len("\n".join(prompt_parts)),
        "has_image": bool(body.image)
    }))

    advice, product_recs = await llm_service.get_style_advice_with_products(
        product_name=product_name,
        product_category=product_category,
        user_question=body.question,
        user_context=user_context,
        available_products=products_dict,
        user_id=user.user_id if user else None,
        image_base64=body.image,
    )

    product_lookup = {p.id: p for p in products}

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

    return {"advice": advice, "products": recommended_products, "product_id": body.product_id, "daily_usage": daily_usage_response}


@router.post("/chat/stream")
async def style_chat_stream(
    request: Request,
    body: ChatRequest,
    user: dict = Depends(optional_auth),
):
    """Get style advice via chat with SSE streaming."""
    from services.model_router import ModelRouter, TaskType

    if not body.question:
        raise HTTPException(status_code=400, detail="Question is required")

    db = get_db(request)
    router = ModelRouter(request.app.state.env)

    # Check LLM usage limit for authenticated users
    is_premium = False
    daily_usage_response = None
    if user:
        user_obj = await db.get_user_by_id(user.user_id)
        is_premium = getattr(user_obj, 'is_premium', False) or getattr(user_obj, 'plan_type', 'free') == 'premium'

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        effective_limit = -1 if is_premium else LLM_DAILY_LIMIT_FREE
        usage_result = await db.try_increment_usage(user.user_id, "llm", today, effective_limit)

        if not usage_result["allowed"]:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "usage_limit_exceeded",
                    "message": f"Límite diario de recomendaciones alcanzado ({LLM_DAILY_LIMIT_FREE}/{LLM_DAILY_LIMIT_FREE})",
                    "current": LLM_DAILY_LIMIT_FREE,
                    "limit": LLM_DAILY_LIMIT_FREE,
                    "upgrade_url": "/payment/upgrade",
                },
            )

        new_llm = usage_result["new_count"]
        daily_usage_response = {
            "vton": 0,
            "llm": new_llm,
            "limit": effective_limit,
            "plan_type": getattr(user_obj, 'plan_type', 'free'),
        }
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

    # Build RAG query
    query = f"{product_name} {product_category} {body.question}"

    # Build filters for RAG
    rag_filters = {}
    if user_obj and user_obj.body_measurements:
        rag_filters["gender"] = user_obj.body_measurements.get("gender")
    if user_obj and user_obj.preferences:
        if user_obj.preferences.get("colors"):
            rag_filters["colors"] = user_obj.preferences["colors"]
        if user_obj.preferences.get("min_price"):
            rag_filters["min_price"] = user_obj.preferences["min_price"]
        if user_obj.preferences.get("max_price"):
            rag_filters["max_price"] = user_obj.preferences["max_price"]

    # Semantic search via RAG
    rag_results = await db.get_rag_products(query=body.question, top_k=10, filters=rag_filters)

    # Build product list for LLM
    rag_products = []
    if rag_results:
        sample_size = min(15, len(rag_results))
        sampled_products = random.sample(rag_results, sample_size) if len(rag_results) > sample_size else rag_results
        products_text = json.dumps(
            [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "store": p["store"],
                    "price": p["price"],
                    "category": p.get("category", ""),
                    "colors": p.get("colors", []),
                }
                for p in sampled_products
            ],
            ensure_ascii=False,
            indent=2,
        )
    else:
        sampled_products = products_dict[:15]
        products_text = json.dumps(
            [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "store": p["store"],
                    "price": p["price"],
                    "category": p.get("category", ""),
                    "colors": p.get("colors", []),
                }
                for p in sampled_products
            ],
            ensure_ascii=False,
            indent=2,
        )

    prompt_parts = [
        f"Producto: {product_name} (categoría: {product_category})",
        f"Pregunta del usuario: {body.question}",
    ]
    if user_context:
        prompt_parts.append(user_context)

    if rag_results:
        prompt_parts.append(f"\nProductos disponibles (SOLO puedes recomendar de esta lista):\n{products_text}")

    prompt_parts.append(
        "\n\nResponde directamente a la pregunta del usuario. "
        "SOLO si el usuario pide recomendaciones explícitamente, menciona productos usando "
        "[**NOMBRE**](/product/ID) con el id exacto de la lista. "
        "Personaliza según los datos del usuario si los tienes. "
        "Responde SOLO texto natural, sin JSON ni formato especial."
    )

    model = "@cf/meta/llama-4-scout-17b-16e-instruct"
    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(prompt_parts)},
    ]

    if body.image:
        clean_base64 = body.image.split(",")[-1] if "," in body.image else body.image
        model = "@cf/meta/llama-4-scout-17b-16e-instruct"
        messages = [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "\n".join(prompt_parts)},
                    {"type": "image_base64", "image_base64": clean_base64}
                ]
            }
        ]

    print(json.dumps({
        "event": "llm_request",
        "method": "style_chat_stream",
        "model": model,
        "prompt_length": len("\n".join(prompt_parts)),
        "has_image": bool(body.image)
    }))

    from services.model_router import ModelRouter, TaskType
    router = ModelRouter(request.app.state.env)

    async def event_generator():
        try:
            # Use model router for streaming
            async for chunk in router.run_stream(
                task_type=TaskType.STYLE_ADVICE,
                messages=[
                    {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                    {"role": "user", "content": "\n".join(prompt_parts)},
                ],
                is_premium=is_premium,
                max_tokens=1024,
                temperature=0.7,
            ):
                # Parse chunk for content
                if isinstance(chunk, dict) and "content" in chunk:
                    payload = json.dumps({"content": chunk["content"]})
                    yield f"data: {payload}\n\n"
                elif isinstance(chunk, str):
                    payload = json.dumps({"content": chunk})
                    yield f"data: {payload}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_payload = json.dumps({"content": str(e)})
            yield f"data: {error_payload}\n\n"

        yield "data: [DONE]\n\n"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(event_generator(), media_type="text/event-stream")
