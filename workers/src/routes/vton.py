"""Virtual Try-On routes."""

import base64
import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
import js
from pyodide.ffi import to_js as _to_js
from js import Object


def to_js(obj):
    """Convert Python objects to JS with dict_converter for proper dict→Object mapping."""
    return _to_js(obj, dict_converter=Object.fromEntries)

from models.vton_result import VtonResult, VtonStatus, VtonHistoryResponse
from services.vton import VtonService, _validate_image, _detect_content_type
from services.image_compressor import ImageCompressor
from middleware.security import require_auth


def _map_category(product_category: str) -> str:
    """Map product category to IDM-VTON category."""
    cat = (product_category or "").lower()
    if any(k in cat for k in ["pantalón", "pantalon", "bottom", "jean", "pant", "short", "bermuda"]):
        return "lower_body"
    if any(k in cat for k in ["vestido", "dress"]):
        return "dresses"
    return "upper_body"


router = APIRouter()

MAX_UPLOAD_BYTES = 100 * 1024  # 100KB


class UploadRequest(BaseModel):
    image: str  # data:image/jpeg;base64,...


class TryOnRequest(BaseModel):
    product_id: str
    user_image_url: str  # data URL from /upload


def get_db(request: Request):
    """Get database service from request state."""
    return request.app.state.db


def _parse_data_url(data_url: str) -> tuple:
    """Parse a data URL and return (mime_type, image_bytes)."""
    if not data_url.startswith("data:"):
        raise HTTPException(status_code=400, detail="Invalid image format. Expected a data URL.")

    header, encoded = data_url.split(",", 1)
    mime = header.split(";")[0].replace("data:", "")
    if not mime.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    try:
        image_bytes = base64.b64decode(encoded)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 data.")

    return mime, image_bytes


def _bytes_to_data_url(data: bytes, content_type: str) -> str:
    """Convert raw bytes back to a data URL."""
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{content_type};base64,{b64}"


async def _fetch_garment_as_data_url(image_url: str) -> str:
    """Download garment image from external CDN and return as data URL.

    CDNs like Zara block non-browser requests to Replicate, so we download
    the image on our server and pass it as a data URL instead.
    Converts via JSON.stringify(Uint8Array) → Python list of ints → bytes.
    """
    resp = await js.fetch(image_url, to_js({"method": "GET"}))
    if resp.status != 200:
        raise Exception(f"Failed to fetch garment image: HTTP {resp.status}")
    buf = await resp.arrayBuffer()
    # .to_py() is a method on JsProxy, not a standalone import
    py_bytes = bytes(buf.to_py())
    b64 = base64.b64encode(py_bytes).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


@router.post("/upload")
async def upload_image(
    request: Request,
    body: UploadRequest,
    user: dict = Depends(require_auth),
):
    """Compress user image and return a data URL. No R2 storage needed."""
    mime, image_bytes = _parse_data_url(body.image)

    if not _validate_image(image_bytes):
        raise HTTPException(
            status_code=400,
            detail="Invalid image format. Please upload a JPEG, PNG, or WebP file.",
        )

    compressor = ImageCompressor(max_bytes=MAX_UPLOAD_BYTES)

    try:
        image_bytes = compressor.compress(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large ({len(image_bytes) // 1024}KB) even after compression. "
                   "Maximum is 100KB. Try a simpler photo with less detail.",
        )

    data_url = _bytes_to_data_url(image_bytes, mime)
    return {"image_url": data_url}


@router.post("/try-on")
async def try_on(
    request: Request,
    body: TryOnRequest,
    user: dict = Depends(require_auth),
):
    """Process virtual try-on. Passes data URL directly to Replicate."""
    user_id = user.user_id
    db = get_db(request)
    vton_service = VtonService(request.app.state.env)

    product = await db.get_product(body.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product.image_url:
        raise HTTPException(status_code=400, detail="Product has no image available for try-on")

    # Download garment image as data URL (CDNs block Replicate's servers)
    try:
        garment_data_url = await _fetch_garment_as_data_url(product.image_url)
    except Exception as e:
        import traceback
        print(json.dumps({"step": "fetch_garment", "error": str(e), "traceback": traceback.format_exc()}))
        raise HTTPException(status_code=500, detail=f"Failed to fetch product image: {e}")

    try:
        vton_result = await db.create_vton_result({
            "user_id": user_id,
            "product_id": body.product_id,
            "status": "processing",
            "input_image_url": body.user_image_url,
            "garment_image_url": garment_data_url[:100] + "...",
        })
    except Exception as e:
        import traceback
        print(json.dumps({"step": "create_vton_result", "error": str(e), "traceback": traceback.format_exc()}))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create try-on record. Please try again. ({e})",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create try-on record. Please try again. ({e})",
        )

    try:
        result = await vton_service.process_try_on(
            user_image_url=body.user_image_url,
            garment_image_url=garment_data_url,
            product_id=body.product_id,
            user_id=user_id,
            category=_map_category(product.category),
        )
    except Exception as e:
        import traceback
        print(json.dumps({"step": "process_try_on", "error": str(e), "traceback": traceback.format_exc()}))
        raise HTTPException(status_code=500, detail=f"VTON processing failed: {e}")

    if result["status"] == "failed":
        await db.update_vton_result(vton_result.id, {
            "status": "failed",
            "error_message": result.get("error", "VTON processing failed"),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        raise HTTPException(status_code=500, detail=result.get("error", "VTON processing failed"))

    # Use the Replicate output URL directly — no R2 re-upload
    output_image_url = result.get("output_url")
    if not output_image_url:
        await db.update_vton_result(vton_result.id, {
            "status": "failed",
            "error_message": "No output URL returned from VTON model",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        raise HTTPException(status_code=500, detail="No output URL returned from VTON model")

    await db.update_vton_result(vton_result.id, {
        "status": "completed",
        "output_image_url": output_image_url,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "id": vton_result.id,
        "status": "completed",
        "output_image_url": output_image_url,
    }


@router.get("/result/{vton_id}")
async def get_result(request: Request, vton_id: str, user: dict = Depends(require_auth)):
    """Get the result of a VTON request."""
    db = get_db(request)
    result = await db.get_vton_result(vton_id)
    if not result:
        raise HTTPException(status_code=404, detail="VTON result not found")
    if result.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "id": result.id,
        "status": result.status,
        "input_image_url": result.input_image_url,
        "output_image_url": result.output_image_url,
        "error_message": result.error_message,
        "created_at": result.created_at,
    }


@router.get("/history")
async def get_history(request: Request, user: dict = Depends(require_auth)):
    """Get VTON history for the authenticated user."""
    db = get_db(request)
    results = await db.get_vton_history(user.user_id)

    return VtonHistoryResponse(
        results=[
            VtonResult(
                id=r.id,
                user_id=r.user_id,
                product_id=r.product_id,
                status=VtonStatus(r.status),
                input_image_url=r.input_image_url,
                output_image_url=r.output_image_url,
                garment_image_url=r.garment_image_url,
                error_message=r.error_message,
                created_at=r.created_at,
            )
            for r in results
        ],
        total=len(results),
    )
