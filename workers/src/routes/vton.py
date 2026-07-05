"""Virtual Try-On API routes — YouCam AI Clothes V3.0 integration.

Optimized Flow:
  1. POST /prefetch  — upload user photo to freeimage.host (call before try-on)
  2. POST /try-on    — create YouCam task with pre-uploaded URL
  3. POST /webhook   — receive YouCam completion notification (no polling needed)
  4. GET  /result/{id} — get result (fallback if webhook missed)
  5. GET  /image/{id} — serves user photo as JPEG
  6. GET  /history   — user's VTON history (images stored in R2)
"""

from fastapi import APIRouter, HTTPException, Request, Query, Depends
from fastapi.responses import Response
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
    """Infer garment category from product tags and name."""
    tags = []
    if hasattr(product, "tags") and product.tags:
        tags = product.tags
    elif isinstance(product, dict):
        tags = product.get("tags", [])

    name = ""
    if hasattr(product, "name"):
        name = product.name.lower()
    elif isinstance(product, dict):
        name = product.get("name", "").lower()

    category = ""
    if hasattr(product, "category"):
        category = product.category.lower() if product.category else ""
    elif isinstance(product, dict):
        category = product.get("category", "").lower()

    combined = ""
    if isinstance(tags, str):
        tags = _parse_json_field(tags)
    if tags:
        combined = " ".join([t.lower() for t in tags if isinstance(t, str)])
    combined += f" {name} {category}"

    # Full body (CHECK FIRST — "vest" is substring of "vestido")
    if any(k in combined for k in ["dress", "suit", "overalls", "jumpsuit", "vestido", "enterizo", "mono"]):
        return "full_body"
    # Lower body
    if any(k in combined for k in ["pant", "jean", "skirt", "trouser", "short", "legging", "falda", "bermuda", "cargo"]):
        return "lower_body"
    # Upper body
    if any(k in combined for k in ["shirt", "blouse", "polo", "sweater", "hoodie", "jacket", "vest", "top", "camisa", "polera", "polerón", "abrig", "chaqueta", "suéter", "cropped"]):
        return "upper_body"

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


@router.post("/prefetch")
async def prefetch_image(
    request_body: dict,
    request: Request,
    user=Depends(require_auth),
):
    """Pre-upload user photo to freeimage.host before try-on."""
    image = request_body.get("image")
    if not image:
        raise HTTPException(status_code=400, detail="image is required")

    raw_b64 = image
    if raw_b64.startswith("data:image"):
        raw_b64 = raw_b64.split(",", 1)[1]

    from services.image_upload import upload_user_photo
    try:
        public_url = await upload_user_photo(raw_b64)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Image upload failed: {str(e)}"
        )

    return {"public_url": public_url, "status": "uploaded"}


@router.post("/prefetch-garment")
async def prefetch_garment(
    request_body: dict,
    request: Request,
    user=Depends(require_auth),
):
    """Pre-upload garment image to freeimage.host before try-on."""
    garment_url = request_body.get("url")
    if not garment_url:
        raise HTTPException(status_code=400, detail="url is required")

    from services.image_upload import upload_garment_image
    try:
        public_url = await upload_garment_image(garment_url)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Garment upload failed: {str(e)}"
        )

    return {"public_url": public_url, "status": "uploaded"}


@router.post("/debug-garment")
async def debug_garment(
    request_body: dict,
    request: Request,
):
    """Test whether YouCam accepts a garment URL.

    Sends the garment URL to YouCam with a transparent 1x1 PNG placeholder
    user image. Returns whether the task was accepted or rejected, and why.
    No auth required (debug endpoint).
    """
    garment_url = request_body.get("garment_url")
    if not garment_url:
        raise HTTPException(status_code=400, detail="garment_url is required")

    env = getattr(request.app.state, "env", None)
    if not env:
        raise HTTPException(status_code=500, detail="Service unavailable")

    # Use a transparent 1x1 PNG as placeholder user image
    placeholder_user_url = "https://upload.wikimedia.org/wikipedia/commons/c/c0/Transparent_base64.png"

    try:
        # Upload garment to freeimage.host first
        from services.image_upload import upload_garment_image
        garment_public_url = await upload_garment_image(garment_url)
    except Exception as e:
        return {
            "accepted": False,
            "error": f"Garment upload to freeimage.host failed: {str(e)}",
            "garment_url": garment_url,
            "garment_public_url": None,
        }

    try:
        youcam = YouCamService(env=env)
        task_id = await youcam.create_task(
            src_url=placeholder_user_url,
            ref_url=garment_public_url,
            garment_category="auto",
        )

        # Poll immediately to check if task was rejected
        import asyncio
        await asyncio.sleep(2)
        result = await youcam.poll_task(task_id)

        return {
            "accepted": result["status"] != "failed",
            "task_id": task_id,
            "status": result["status"],
            "error": result.get("error"),
            "garment_url": garment_url,
            "garment_public_url": garment_public_url,
        }

    except Exception as e:
        return {
            "accepted": False,
            "error": f"YouCam API error: {str(e)}",
            "garment_url": garment_url,
            "garment_public_url": garment_public_url,
        }


@router.get("/image/{vton_id}")
async def serve_image(vton_id: str, request: Request):
    """Serve user photo as JPEG for YouCam to fetch. No auth (public endpoint)."""
    from services.database import DatabaseService

    env = getattr(request.app.state, "env", None)
    if not env:
        raise HTTPException(status_code=500, detail="Service unavailable")
    db = DatabaseService(env)
    vton_result = await db.get_vton_result(vton_id)
    if not vton_result:
        raise HTTPException(status_code=404, detail="Image not found")
    if not vton_result.input_image_url:
        raise HTTPException(status_code=404, detail="No image data")

    data_url = vton_result.input_image_url
    if data_url.startswith("data:image"):
        header, b64data = data_url.split(",", 1)
        img_bytes = base64.b64decode(b64data)
        return Response(content=img_bytes, media_type="image/jpeg")
    else:
        raise HTTPException(status_code=400, detail="Invalid image format")


@router.post("/try-on")
async def try_on(
    request_body: dict,
    request: Request,
    user=Depends(require_auth),
):
    """Request virtual try-on via YouCam V3.0."""
    product_id = request_body.get("product_id")
    user_image_url = request_body.get("user_image_url")
    public_url = request_body.get("public_url")
    garment_public_url = request_body.get("garment_public_url")

    if not product_id or not user_image_url:
        raise HTTPException(
            status_code=400, detail="product_id and user_image_url are required"
        )

    user_id = user.user_id
    db = get_db(request)
    env = get_env(request)

    try:
        product = await db.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        garment_url = _extract_garment_url(product)
        if not garment_url:
            raise HTTPException(status_code=400, detail="Product has no images")

        garment_category = _extract_garment_category(product)

        if not public_url:
            raw_b64 = user_image_url
            if raw_b64.startswith("data:image"):
                raw_b64 = raw_b64.split(",", 1)[1]
            from services.image_upload import upload_user_photo
            public_url = await upload_user_photo(raw_b64)

        if not garment_public_url:
            from services.image_upload import upload_garment_image
            garment_public_url = await upload_garment_image(garment_url)

        vton_result = await db.create_vton_result({
            "user_id": user_id,
            "product_id": product_id,
            "status": "pending",
            "input_image_url": user_image_url,
            "garment_image_url": garment_url[:500] if garment_url else None,
        })
        vton_id = vton_result.id

        youcam = YouCamService(env=env)
        task_id = await youcam.create_task(
            src_url=public_url,
            ref_url=garment_public_url,
            garment_category=garment_category,
        )

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


@router.post("/webhook")
async def youcam_webhook(request: Request):
    """Receive YouCam webhook notification when task completes."""
    body = await request.body()
    payload = body.decode("utf-8")

    signature = request.headers.get("webhook-signature", "")
    webhook_id = request.headers.get("webhook-id", "")
    webhook_ts = request.headers.get("webhook-timestamp", "")

    env = getattr(request.app.state, "env", None)
    if not env:
        return {"status": "error", "detail": "Service unavailable"}

    webhook_secret = getattr(env, "YOUCAM_WEBHOOK_SECRET", "")
    if webhook_secret:
        if not YouCamService.verify_webhook_signature(payload, signature, webhook_secret):
            return {"status": "error", "detail": "Invalid signature"}

    try:
        data = json.loads(payload)
        task_id = data.get("data", {}).get("task_id")
        task_status = data.get("data", {}).get("task_status")

        if not task_id:
            return {"status": "error", "detail": "No task_id"}

        from services.database import DatabaseService
        db = DatabaseService(env)

        vton_result = await db.get_vton_by_task_id(task_id)
        if not vton_result:
            return {"status": "ok", "detail": "Task not found in D1 (may be old)"}

        if task_status == "success":
            results = data.get("data", {}).get("results", {})
            output_url = ""
            if isinstance(results, dict):
                output_url = results.get("url") or results.get("image_url") or ""
            elif isinstance(results, list) and results:
                output_url = results[0]

            # Save output to R2 for persistent storage
            from services.r2 import save_vton_output_to_r2
            r2_url = await save_vton_output_to_r2(env, vton_result.user_id, vton_result.id, output_url)

            await db.update_vton_result(vton_result.id, {
                "status": "completed",
                "output_image_url": r2_url,
                "completed_at": datetime.utcnow().isoformat(),
            })
        elif task_status == "error":
            error = data.get("data", {}).get("error", "YouCam task failed")
            await db.update_vton_result(vton_result.id, {
                "status": "failed",
                "error_message": error,
                "completed_at": datetime.utcnow().isoformat(),
            })

        return {"status": "ok"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "detail": str(e)}


@router.get("/result/{vton_id}")
async def get_result(
    vton_id: str,
    request: Request,
    user=Depends(require_auth),
):
    """Get VTON result status. Polls YouCam directly if task still processing."""
    user_id = user.user_id
    db = get_db(request)
    env = get_env(request)
    vton_result = await db.get_vton_result(vton_id)

    if not vton_result:
        raise HTTPException(status_code=404, detail="VTON result not found")
    if vton_result.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # If still processing, poll YouCam directly and update D1
    if vton_result.status == "processing" and vton_result.youcam_task_id:
        try:
            youcam = YouCamService(env=env)
            result = await youcam.poll_task(vton_result.youcam_task_id)

            if result["status"] == "completed":
                output_url = result.get("output_url", "")

                # Save output to R2 for persistent storage
                from services.r2 import save_vton_output_to_r2
                r2_url = await save_vton_output_to_r2(env, user_id, vton_id, output_url)

                await db.update_vton_result(vton_id, {
                    "status": "completed",
                    "output_image_url": r2_url,
                    "completed_at": datetime.utcnow().isoformat(),
                })
                vton_result.status = "completed"
                vton_result.output_image_url = r2_url

            elif result["status"] == "failed":
                await db.update_vton_result(vton_id, {
                    "status": "failed",
                    "error_message": result.get("error", "YouCam task failed"),
                    "completed_at": datetime.utcnow().isoformat(),
                })
                vton_result.status = "failed"
                vton_result.error_message = result.get("error")
        except Exception as e:
            import traceback
            traceback.print_exc()

    return {
        "status": vton_result.status,
        "output_image_url": vton_result.output_image_url,
        "error": vton_result.error_message,
    }


@router.get("/history")
async def get_user_history(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    user=Depends(require_auth),
):
    """Get user's VTON results (images stored in R2)."""
    user_id = user.user_id
    db = get_db(request)
    results = await db.get_vton_history(user_id, limit=limit)

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
                    "store": product.store,
                    "price": product.price,
                    "original_url": product.original_url,
                }
        response_results.append(entry)

    return {"results": response_results, "total": len(response_results)}
