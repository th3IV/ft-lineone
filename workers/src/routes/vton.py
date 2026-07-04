"""Virtual Try-On API routes — YouCam AI Clothes V3.0 integration.

Flow:
  1. POST /upload   — accepts base64, returns data URL (identity, for compatibility)
  2. POST /try-on   — sends user photo + garment URL to YouCam, returns task id
  3. GET  /result/{id} — polls YouCam for result
  4. GET  /history  — user's VTON history
"""

from fastapi import APIRouter, HTTPException, Request, Query, Depends
import base64
import json
from datetime import datetime

from models.vton_result import VtonStatus
from services.auth import verify_token
from services.youcam import YouCamService
from middleware.security import require_auth

router = APIRouter()


def get_db(request: Request):
    """Get database service from request state."""
    return request.app.state.db


def get_env(request: Request):
    """Get Workers env binding from request state."""
    return getattr(request.app.state, "env", None)


def _parse_json_field(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


def _extract_garment_url(product) -> str:
    """Extract first image URL from a product model or row dict."""
    if hasattr(product, "image_urls") and product.image_urls:
        images = product.image_urls
    elif hasattr(product, "image_url") and product.image_url:
        return str(product.image_url)
    elif isinstance(product, dict):
        images = product.get("image_urls") or product.get("image_url")
    else:
        return ""
    if not images:
        return ""
    if isinstance(images, str):
        images = _parse_json_field(images)
    if images:
        url = images[0] if isinstance(images, list) else images
        if isinstance(url, dict):
            url = url.get("src") or url.get("url") or ""
        return str(url)
    return ""


def _extract_garment_category(product) -> str:
    """Infer garment category from product tags."""
    if hasattr(product, "tags"):
        tags = product.tags
    else:
        tags = product.get("tags") if isinstance(product, dict) else None
    if not tags:
        return "auto"
    if isinstance(tags, str):
        tags = _parse_json_field(tags)
    tag_lower = " ".join([t.lower() for t in tags if isinstance(t, str)])

    if any(k in tag_lower for k in ["shoe", "sneaker", "boot", "sandal", "slipper"]):
        return "shoes"
    if any(k in tag_lower for k in ["pant", "jean", "skirt", "trouser", "short", "legging"]):
        return "lower_body"
    return "auto"


@router.post("/upload")
async def upload_image(request_body: dict):
    """Accept base64 image, return data URL. Kept for frontend compatibility."""
    image = request_body.get("image")
    if not image:
        raise HTTPException(status_code=400, detail="image is required")

    if not image.startswith("data:image"):
        image = f"data:image/jpeg;base64,{image}"

    return {"image_url": image, "status": "uploaded"}


@router.post("/try-on")
async def try_on(
    request_body: dict,
    request: Request,
    user=Depends(require_auth),
):
    """Request virtual try-on via YouCam V3.0.

    Accepts: { product_id, user_image_url }
    user_image_url is a data URL from the /upload endpoint.

    V3.0 workflow (simplified — no File API, no byte uploads):
      1. Get product image URL from DB
      2. POST /v3.0/task/cloth with { src_file_url, ref_file_url, garment_category }
      3. Return { id, status: "processing" } for frontend to poll
    """
    product_id = request_body.get("product_id")
    user_image_url = request_body.get("user_image_url")

    if not product_id or not user_image_url:
        raise HTTPException(
            status_code=400, detail="product_id and user_image_url are required"
        )

    user_id = user.user_id
    db = get_db(request)

    try:
        # Get product
        product = await db.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        garment_url = _extract_garment_url(product)
        if not garment_url:
            raise HTTPException(status_code=400, detail="Product has no images")

        garment_category = _extract_garment_category(product)

        # Create VTON result record
        vton_result = await db.create_vton_result({
            "user_id": user_id,
            "product_id": product_id,
            "status": "pending",
            "input_image_url": user_image_url[:500] if user_image_url else None,
            "garment_image_url": garment_url[:500] if garment_url else None,
        })
        vton_id = vton_result.id

        # Create YouCam task (V3.0 — direct URLs, no byte uploads)
        youcam = YouCamService(env=get_env(request))
        task_id = await youcam.create_task(
            src_url=user_image_url,
            ref_url=garment_url,
            garment_category=garment_category,
        )

        # Store task ID
        await db.update_vton_result(vton_id, {
            "youcam_task_id": task_id,
            "status": "processing",
        })

        return {"id": vton_id, "status": "processing"}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"VTON request failed: {str(e)}"
        )


@router.get("/result/{vton_id}")
async def get_result(
    vton_id: str,
    request: Request,
    user=Depends(require_auth),
):
    """Poll YouCam task status. Frontend calls this every 4s."""
    user_id = user.user_id
    db = get_db(request)
    vton_result = await db.get_vton_result(vton_id)

    if not vton_result:
        raise HTTPException(status_code=404, detail="VTON result not found")
    if vton_result.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Already terminal — return cached
    if vton_result.status in (VtonStatus.COMPLETED.value, VtonStatus.FAILED.value):
        return {
            "status": vton_result.status,
            "output_image_url": vton_result.output_image_url,
            "error": vton_result.error_message,
        }

    # No YouCam task yet — still pending
    if not vton_result.youcam_task_id:
        return {"status": "processing"}

    # Poll YouCam
    youcam = YouCamService(env=get_env(request))
    try:
        result = await youcam.poll_task(vton_result.youcam_task_id)

        if result["status"] == "completed":
            await db.update_vton_result(vton_id, {
                "status": VtonStatus.COMPLETED.value,
                "output_image_url": result["output_url"],
                "completed_at": datetime.utcnow().isoformat(),
            })
            return {
                "status": VtonStatus.COMPLETED.value,
                "output_image_url": result["output_url"],
            }

        if result["status"] == "failed":
            await db.update_vton_result(vton_id, {
                "status": VtonStatus.FAILED.value,
                "error_message": result.get("error", "YouCam task failed"),
                "completed_at": datetime.utcnow().isoformat(),
            })
            return {
                "status": VtonStatus.FAILED.value,
                "error": result.get("error", "YouCam task failed"),
            }

        return {"status": "processing"}

    except Exception:
        return {"status": "processing"}


@router.get("/history")
async def get_user_history(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    user=Depends(require_auth),
):
    """Get user's VTON results."""
    user_id = user.user_id
    db = get_db(request)
    results = await db.get_vton_history(user_id, limit)

    response_results = []
    for r in results:
        entry = {
            "id": r.id,
            "status": r.status,
            "product_id": r.product_id,
            "input_image_url": r.input_image_url,
            "output_image_url": r.output_image_url,
            "error_message": r.error_message,
            "created_at": r.created_at,
            "completed_at": r.completed_at,
        }

        if r.product_id:
            product = await db.get_product(r.product_id)
            if product:
                img = _extract_garment_url(product)
                entry["product"] = {
                    "id": product.id,
                    "name": product.name,
                    "image": img,
                }
        response_results.append(entry)

    return {"results": response_results}
