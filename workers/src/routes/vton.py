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
from datetime import datetime, timezone

from models.vton_result import VtonStatus
from services.auth import verify_token
from services.config import VTON_DAILY_LIMIT_FREE, MAX_USER_IMAGE_BYTES, ALLOWED_IMAGE_MAGIC
from services.youcam import YouCamService
from middleware.security import require_auth, require_admin, optional_auth, safe_error_message

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


def _validate_user_image(b64_data: str) -> bytes:
    """Decode base64 image, validate magic bytes + size. Returns decoded bytes or raises HTTPException."""
    import base64 as _b64
    try:
        image_bytes = _b64.b64decode(b64_data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image data: could not decode base64")

    if len(image_bytes) > MAX_USER_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail=f"Image too large: maximum {MAX_USER_IMAGE_BYTES // (1024*1024)}MB")

    header = image_bytes[:8]
    if not any(header.startswith(magic) for magic in ALLOWED_IMAGE_MAGIC):
        raise HTTPException(status_code=400, detail="Invalid image format: only JPEG, PNG, WebP, and HEIC are allowed")

    return image_bytes


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
async def upload_image(request_body: dict, user=Depends(require_auth)):
    """[DEPRECATED] Accept base64 image, return data URL. Use POST /generate instead."""
    image = request_body.get("image")
    if not image:
        raise HTTPException(status_code=400, detail="image is required")

    if not image.startswith("data:image"):
        image = f"data:image/jpeg;base64,{image}"

    return {"image_url": image, "status": "uploaded"}


@router.post("/generate")
async def generate_try_on(
    request_body: dict,
    request: Request,
    user=Depends(require_auth),
):
    """Consolidated VTON endpoint — single call replaces /prefetch + /try-on.

    Accepts:
      - product_id (required)
      - image (required): base64 user photo (with or without data:image prefix)
      - garment_url (optional): override garment image URL

    Returns:
      - id: vton_id for polling /result/{id}
      - status: "processing"
      - daily_usage: { vton, llm, limit, plan_type }
    """
    product_id = request_body.get("product_id")
    image = request_body.get("image")

    if not product_id or not image:
        raise HTTPException(status_code=400, detail="product_id and image are required")

    user_id = user.user_id
    db = get_db(request)
    env = get_env(request)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    user_obj = await db.get_user_by_id(user_id)
    is_premium = getattr(user_obj, 'is_premium', False) or getattr(user_obj, 'plan_type', 'free') == 'premium'

    import time as _time

    try:
        product = await db.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        garment_url = request_body.get("garment_url") or _extract_garment_url(product)
        if not garment_url:
            raise HTTPException(status_code=400, detail="Product has no images")

        garment_category = _extract_garment_category(product)

        raw_b64 = image
        if raw_b64.startswith("data:image"):
            raw_b64 = raw_b64.split(",", 1)[1]
        _validate_user_image(raw_b64)

        t0 = _time.time()
        from services.image_upload import upload_user_photo, upload_garment_image
        public_url = await upload_user_photo(raw_b64, env=env)
        print(json.dumps({"event": "generate_user_upload", "latency_ms": int((_time.time() - t0) * 1000)}))

        t0 = _time.time()
        garment_public_url = await upload_garment_image(garment_url, env=env)
        print(json.dumps({"event": "generate_garment_upload", "latency_ms": int((_time.time() - t0) * 1000)}))

        vton_result = await db.create_vton_result({
            "user_id": user_id,
            "product_id": product_id,
            "status": "pending",
            "input_image_url": public_url,
            "garment_image_url": garment_url[:500] if garment_url else None,
        })
        vton_id = vton_result.id

        youcam = YouCamService(env=env)
        t0 = _time.time()
        task_id = await youcam.create_task(
            src_url=public_url,
            ref_url=garment_public_url,
            garment_category=garment_category,
        )
        print(json.dumps({"event": "generate_youcam_created", "task_id": task_id[:20], "latency_ms": int((_time.time() - t0) * 1000)}))

        await db.update_vton_result(vton_id, {
            "youcam_task_id": task_id,
            "status": "processing",
        })

        effective_limit = -1 if is_premium else VTON_DAILY_LIMIT_FREE
        result = await db.try_increment_usage(user_id, "vton", today, effective_limit)
        new_vton = result["new_count"]

        if not result["allowed"]:
            await db.delete_vton_result(vton_id, user_id)
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "usage_limit_exceeded",
                    "message": f"Límite diario de VTON alcanzado ({VTON_DAILY_LIMIT_FREE}/{VTON_DAILY_LIMIT_FREE})",
                    "current": VTON_DAILY_LIMIT_FREE,
                    "limit": VTON_DAILY_LIMIT_FREE,
                    "upgrade_url": "/payment/upgrade",
                },
            )

        usage = await db.get_user_usage_readonly(user_id, today) if not is_premium else {"vton_count": 0, "llm_count": 0}

        return {
            "id": vton_id,
            "status": "processing",
            "daily_usage": {
                "vton": new_vton,
                "llm": usage.get("llm_count", 0),
                "limit": effective_limit,
                "plan_type": getattr(user_obj, 'plan_type', 'free'),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback, json as _json
        traceback.print_exc()
        print(_json.dumps({"event": "generate_error", "error": str(e), "error_type": type(e).__name__, "product_id": product_id, "user_id": user_id}))
        raise HTTPException(status_code=500, detail=f"VTON request failed: {safe_error_message(e, request)}")


@router.post("/prefetch")
async def prefetch_image(
    request_body: dict,
    request: Request,
    user=Depends(require_auth),
):
    """[DEPRECATED] Pre-upload user photo to freeimage.host before try-on. Use POST /generate instead."""
    image = request_body.get("image")
    if not image:
        raise HTTPException(status_code=400, detail="image is required")

    env = get_env(request)
    raw_b64 = image
    if raw_b64.startswith("data:image"):
        raw_b64 = raw_b64.split(",", 1)[1]

    _validate_user_image(raw_b64)

    import time as _time
    t0 = _time.time()
    from services.image_upload import upload_user_photo
    try:
        public_url = await upload_user_photo(raw_b64, env=env)
        latency_ms = int((_time.time() - t0) * 1000)
        print(json.dumps({"event": "prefetch_user_ok", "latency_ms": latency_ms, "url_prefix": public_url[:60] if public_url else "none"}))
    except Exception as e:
        latency_ms = int((_time.time() - t0) * 1000)
        print(json.dumps({"event": "prefetch_user_error", "error": str(e), "error_type": type(e).__name__, "latency_ms": latency_ms}))
        raise HTTPException(
            status_code=500, detail=f"Image upload failed: {safe_error_message(e, request)}"
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

    env = get_env(request)
    import time as _time
    t0 = _time.time()
    from services.image_upload import upload_garment_image
    try:
        public_url = await upload_garment_image(garment_url, env=env)
        latency_ms = int((_time.time() - t0) * 1000)
        print(json.dumps({"event": "prefetch_garment_ok", "latency_ms": latency_ms, "url_prefix": public_url[:60] if public_url else "none"}))
    except Exception as e:
        latency_ms = int((_time.time() - t0) * 1000)
        print(json.dumps({"event": "prefetch_garment_error", "error": str(e), "error_type": type(e).__name__, "latency_ms": latency_ms}))
        raise HTTPException(
            status_code=500, detail=f"Garment upload failed: {safe_error_message(e, request)}"
        )

    return {"public_url": public_url, "status": "uploaded"}


@router.post("/debug-garment")
async def debug_garment(
    request_body: dict,
    request: Request,
    user=Depends(require_auth),
):
    """Test whether YouCam accepts a garment URL. Requires auth."""
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


@router.get("/debug-deps")
async def debug_deps(request: Request, user=Depends(require_admin)):
    """Test all VTON dependencies independently. Requires auth."""
    import json as _json
    import time
    env = getattr(request.app.state, "env", None)
    results = {}

    # 1. Test freeimage.host
    t0 = time.time()
    try:
        from services.image_upload import _upload_to_freeimage
        import base64 as _b64
        tiny_pixel = _b64.b64encode(
            bytes([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
                    0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xD9])
        ).decode("ascii")
        url = await _upload_to_freeimage(tiny_pixel, "probe.jpg")
        results["freeimage"] = {"status": "ok", "url": url, "latency_ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        results["freeimage"] = {"status": "error", "error": str(e), "latency_ms": int((time.time() - t0) * 1000)}

    # 2. Test YouCam API key
    t0 = time.time()
    try:
        youcam = YouCamService(env=env)
        # Intentionally use invalid task ID to test auth (404 = key valid, 401 = key invalid)
        import js as _js
        from pyodide.ffi import to_js as _to_js
        from js import Object
        resp = await _js.fetch(
            f"https://yce-api-01.makeupar.com/s2s/v3.0/task/cloth/nonexistent-id",
            _to_js({
                "method": "GET",
                "headers": youcam._auth_headers(),
            }, dict_converter=Object.fromEntries),
        )
        status = int(resp.status)
        if status == 401:
            results["youcam"] = {"status": "error", "error": "API key invalid (401)", "latency_ms": int((time.time() - t0) * 1000)}
        elif status == 404:
            results["youcam"] = {"status": "ok", "detail": "API key valid (404 on fake ID)", "latency_ms": int((time.time() - t0) * 1000)}
        else:
            text = await resp.text()
            results["youcam"] = {"status": "ok", "detail": f"API responded {status}", "latency_ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        results["youcam"] = {"status": "error", "error": str(e), "latency_ms": int((time.time() - t0) * 1000)}

    # 3. Test R2 binding
    t0 = time.time()
    try:
        if env and hasattr(env, "R2"):
            head = await env.R2.head("vton/probe-test.txt")
            results["r2"] = {"status": "ok", "detail": "R2 binding works", "latency_ms": int((time.time() - t0) * 1000)}
        else:
            results["r2"] = {"status": "error", "error": "R2 binding not found"}
    except Exception as e:
        # 404 on head is fine — means R2 is reachable
        if "404" in str(e) or "NoSuchKey" in str(e) or "Not Found" in str(e):
            results["r2"] = {"status": "ok", "detail": "R2 binding works (object not found, but reachable)", "latency_ms": int((time.time() - t0) * 1000)}
        else:
            results["r2"] = {"status": "error", "error": str(e), "latency_ms": int((time.time() - t0) * 1000)}

    all_ok = all(r.get("status") == "ok" for r in results.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "services": results,
    }


@router.get("/health")
async def health(request: Request, user=Depends(optional_auth)):
    """Health check for VTON dependencies. Auth optional (for monitoring)."""
    import time
    env = getattr(request.app.state, "env", None)
    services = {}

    # freeimage.host — lightweight check (just verify endpoint reachable)
    t0 = time.time()
    try:
        import js as _js
        from pyodide.ffi import to_js as _to_js
        from js import Object
        resp = await _js.fetch(
            "https://freeimage.host/api/1/upload",
            _to_js({"method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "body": "key=test&format=json"}, dict_converter=Object.fromEntries),
        )
        # Any response means the service is reachable
        services["freeimage"] = {"status": "ok" if int(resp.status) < 500 else "error", "latency_ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        services["freeimage"] = {"status": "error", "error": str(e)[:100], "latency_ms": int((time.time() - t0) * 1000)}

    # YouCam — lightweight check
    t0 = time.time()
    try:
        youcam = YouCamService(env=env)
        services["youcam"] = {"status": "ok" if youcam.api_key else "error", "detail": "key present" if youcam.api_key else "key missing"}
    except Exception as e:
        services["youcam"] = {"status": "error", "error": str(e)[:100]}

    # R2
    t0 = time.time()
    try:
        if env and hasattr(env, "R2"):
            await env.R2.head("vton/probe-test.txt")
            services["r2"] = {"status": "ok", "latency_ms": int((time.time() - t0) * 1000)}
        else:
            services["r2"] = {"status": "error", "detail": "no binding"}
    except Exception as e:
        services["r2"] = {"status": "ok" if "404" in str(e) or "Not Found" in str(e) else "error", "latency_ms": int((time.time() - t0) * 1000)}

    # D1
    t0 = time.time()
    try:
        db_module = __import__("services.database", fromlist=["DatabaseService"])
        db = db_module.DatabaseService(env)
        await db.db.prepare("SELECT 1 as ok").first()
        services["d1"] = {"status": "ok", "latency_ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        services["d1"] = {"status": "error", "error": str(e)[:100], "latency_ms": int((time.time() - t0) * 1000)}

    all_ok = all(s.get("status") == "ok" for s in services.values())
    return {"status": "healthy" if all_ok else "degraded", "services": services}


@router.get("/image/{vton_id}")
async def serve_image(vton_id: str, request: Request, user=Depends(require_auth)):
    """Serve user photo as JPEG. DEPRECATED — use /history instead.

    YouCam fetches user photos via freeimage.host public URLs (not this endpoint).
    This endpoint is kept for backward compatibility but now requires auth + ownership.
    """
    from services.database import DatabaseService

    env = getattr(request.app.state, "env", None)
    if not env:
        raise HTTPException(status_code=500, detail="Service unavailable")
    db = DatabaseService(env)
    vton_result = await db.get_vton_result(vton_id)
    if not vton_result:
        raise HTTPException(status_code=404, detail="Image not found")
    if vton_result.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
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
    """[DEPRECATED] Request virtual try-on via YouCam V3.0. Use POST /generate instead."""
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

    # Check VTON usage limit (atomic with increment below)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    user_obj = await db.get_user_by_id(user_id)
    is_premium = getattr(user_obj, 'is_premium', False) or getattr(user_obj, 'plan_type', 'free') == 'premium'

    try:
        product = await db.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        garment_url = _extract_garment_url(product)
        if not garment_url:
            raise HTTPException(status_code=400, detail="Product has no images")

        garment_category = _extract_garment_category(product)

        import time as _time

        if not public_url:
            raw_b64 = user_image_url
            if raw_b64.startswith("data:image"):
                raw_b64 = raw_b64.split(",", 1)[1]
            _validate_user_image(raw_b64)
            t0 = _time.time()
            from services.image_upload import upload_user_photo
            public_url = await upload_user_photo(raw_b64, env=env)
            print(json.dumps({"event": "tryon_user_upload", "latency_ms": int((_time.time() - t0) * 1000)}))

        if not garment_public_url:
            t0 = _time.time()
            from services.image_upload import upload_garment_image
            garment_public_url = await upload_garment_image(garment_url, env=env)
            print(json.dumps({"event": "tryon_garment_upload", "latency_ms": int((_time.time() - t0) * 1000)}))

        vton_result = await db.create_vton_result({
            "user_id": user_id,
            "product_id": product_id,
            "status": "pending",
            "input_image_url": user_image_url,
            "garment_image_url": garment_url[:500] if garment_url else None,
        })
        vton_id = vton_result.id

        youcam = YouCamService(env=env)
        t0 = _time.time()
        task_id = await youcam.create_task(
            src_url=public_url,
            ref_url=garment_public_url,
            garment_category=garment_category,
        )
        print(json.dumps({"event": "tryon_youcam_created", "task_id": task_id[:20], "latency_ms": int((_time.time() - t0) * 1000)}))

        await db.update_vton_result(vton_id, {
            "youcam_task_id": task_id,
            "status": "processing",
        })

        # Atomic check-and-increment VTON usage (prevents TOCTOU race)
        effective_limit = -1 if is_premium else VTON_DAILY_LIMIT_FREE
        result = await db.try_increment_usage(user_id, "vton", today, effective_limit)
        new_vton = result["new_count"]

        if not result["allowed"]:
            # Refund the VTON result since increment failed
            await db.delete_vton_result(vton_id, user_id)
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "usage_limit_exceeded",
                    "message": f"Límite diario de VTON alcanzado ({VTON_DAILY_LIMIT_FREE}/{VTON_DAILY_LIMIT_FREE})",
                    "current": VTON_DAILY_LIMIT_FREE,
                    "limit": VTON_DAILY_LIMIT_FREE,
                    "upgrade_url": "/payment/upgrade",
                },
            )

        usage = await db.get_user_usage_readonly(user_id, today) if not is_premium else {"vton_count": 0, "llm_count": 0}

        return {
            "id": vton_id,
            "status": "processing",
            "daily_usage": {
                "vton": new_vton,
                "llm": usage.get("llm_count", 0),
                "limit": effective_limit,
                "plan_type": getattr(user_obj, 'plan_type', 'free'),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback, json as _json
        traceback.print_exc()
        print(_json.dumps({"event": "try_on_error", "error": str(e), "error_type": type(e).__name__, "product_id": product_id, "user_id": user_id}))
        raise HTTPException(
            status_code=500, detail=f"VTON request failed: {safe_error_message(e, request)}"
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
    if not webhook_secret:
        from services.config import YOUCAM_WEBHOOK_FAIL_CLOSED
        if YOUCAM_WEBHOOK_FAIL_CLOSED:
            print(json.dumps({"event": "webhook_rejected", "reason": "no_secret_configured"}))
            return {"status": "error", "detail": "Webhook secret not configured"}
    elif not YouCamService.verify_webhook_signature(payload, signature, webhook_secret):
        print(json.dumps({"event": "webhook_rejected", "reason": "invalid_signature"}))
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

            print(json.dumps({
                "event": "webhook_success",
                "task_id": task_id[:20],
                "output_url_len": len(output_url) if output_url else 0,
                "output_url_prefix": output_url[:80] if output_url else "EMPTY",
                "results_type": type(results).__name__,
            }))

            # Save output to R2 for persistent storage
            from services.r2 import save_vton_output_to_r2
            r2_url = await save_vton_output_to_r2(env, vton_result.user_id, vton_result.id, output_url)

            await db.update_vton_result(vton_result.id, {
                "status": "completed",
                "output_image_url": r2_url,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })
        elif task_status == "error":
            error = data.get("data", {}).get("error", "YouCam task failed")
            await db.refund_vton_usage(vton_result.id, error)

        return {"status": "ok"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "detail": "Webhook processing failed"}


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
    try:
        vton_result = await db.get_vton_result(vton_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save result")

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
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                })
                vton_result.status = "completed"
                vton_result.output_image_url = r2_url

            elif result["status"] == "failed":
                await db.refund_vton_usage(vton_id, result.get("error", "YouCam task failed"))
                vton_result.status = "failed"
                vton_result.error_message = result.get("error")
        except Exception as e:
            import traceback, json
            traceback.print_exc()
            print(json.dumps({"event": "vton_poll_failed", "vton_id": vton_id, "error": str(e)}))
            try:
                await db.refund_vton_usage(vton_id, f"Polling error: {str(e)}")
                vton_result.status = "failed"
                vton_result.error_message = f"Polling error: {str(e)}"
            except Exception:
                pass

    return {
        "status": vton_result.status,
        "output_image_url": vton_result.output_image_url,
        "error": vton_result.error_message,
    }


@router.post("/{vton_id}/persist")
async def persist_vton_result(
    vton_id: str,
    request: Request,
    user=Depends(require_auth),
):
    """Explicitly persist VTON result to R2 (idempotent)."""
    user_id = user.user_id
    db = get_db(request)
    env = get_env(request)
    vton_result = await db.get_vton_result(vton_id)

    if not vton_result:
        raise HTTPException(status_code=404, detail="VTON result not found")
    if vton_result.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if vton_result.status != "completed":
        raise HTTPException(status_code=400, detail="VTON not yet completed")

    output_url = vton_result.output_image_url
    if not output_url:
        raise HTTPException(status_code=400, detail="No output image to persist")

    from services.r2 import R2_PUBLIC_BASE, save_vton_output_to_r2

    if R2_PUBLIC_BASE in output_url:
        return {"status": "already_persisted", "r2_url": output_url}

    try:
        r2_url = await save_vton_output_to_r2(env, user_id, vton_id, output_url)
        if r2_url != output_url:
            await db.update_vton_result(vton_id, {"output_image_url": r2_url})
        return {"status": "persisted", "r2_url": r2_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to persist: {safe_error_message(e, request)}")


@router.delete("/{vton_id}")
async def delete_vton_result_route(
    vton_id: str,
    request: Request,
    user=Depends(require_auth),
):
    """Delete a VTON result (D1 record + R2 object)."""
    user_id = user.user_id
    db = get_db(request)
    env = get_env(request)
    vton_result = await db.get_vton_result(vton_id)

    if not vton_result:
        raise HTTPException(status_code=404, detail="VTON result not found")
    if vton_result.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    from services.r2 import delete_vton_result as delete_r2_object
    try:
        await delete_r2_object(env, user_id, vton_id)
    except Exception as e:
        import json
        print(json.dumps({"event": "r2_delete_failed", "vton_id": vton_id, "error": str(e)}))

    await db.delete_vton_result(vton_id, user_id)
    return {"status": "deleted"}


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


@router.post("/debug-r2-youcam")
async def debug_r2_youcam(request_body: dict, request: Request, user=Depends(require_admin)):
    """Test if YouCam can access R2 public URLs. Requires auth."""
    import time
    r2_url = request_body.get("r2_url", "")
    if not r2_url:
        return {"error": "r2_url is required"}

    env = getattr(request.app.state, "env", None)
    youcam = YouCamService(env=env)

    # Use a tiny 1x1 white JPEG as user photo (data URL)
    tiny_jpeg_b64 = "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AKwA//9k="
    user_photo_url = f"data:image/jpeg;base64,{tiny_jpeg_b64}"

    t0 = time.time()
    try:
        task_id = await youcam.create_task(
            src_url=user_photo_url,
            ref_url=r2_url,
            garment_category="auto",
        )
        latency_ms = int((time.time() - t0) * 1000)
        return {
            "status": "ok",
            "task_id": task_id,
            "message": "YouCam accepted the R2 URL! Task created successfully.",
            "r2_url": r2_url,
            "latency_ms": latency_ms,
        }
    except Exception as e:
        latency_ms = int((time.time() - t0) * 1000)
        return {
            "status": "error",
            "error": str(e),
            "r2_url": r2_url,
            "latency_ms": latency_ms,
            "hint": "If error mentions 'download' or 'fetch', YouCam cannot access R2. If task was created, R2 works!",
        }
