"""Virtual Try-On routes."""

import base64
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from models.vton_result import VtonResult, VtonStatus, VtonHistoryResponse
from services.vton import VtonService, _validate_image
from services.r2 import R2Service
from middleware.security import require_auth

router = APIRouter()

MAX_UPLOAD_BYTES = 100 * 1024  # 100KB — small enough for Pyodide ASGI bridge


class UploadRequest(BaseModel):
    image: str  # data:image/jpeg;base64,...


class TryOnRequest(BaseModel):
    product_id: str
    user_image_url: str  # R2 public URL from /upload


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


@router.post("/upload")
async def upload_image(
    request: Request,
    body: UploadRequest,
    user: dict = Depends(require_auth),
):
    """Upload user image to R2. Returns the public URL."""
    mime, image_bytes = _parse_data_url(body.image)

    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large ({len(image_bytes) // 1024}KB). Maximum is 100KB. "
                   "Please take a photo with simpler background or lower resolution.",
        )

    if not _validate_image(image_bytes):
        raise HTTPException(
            status_code=400,
            detail="Invalid image format. Please upload a JPEG, PNG, or WebP file.",
        )

    user_id = user.user_id
    r2_service = R2Service(request.app.state.env)

    key = f"vton/user-uploads/{user_id}/{uuid.uuid4().hex}.jpg"
    image_url = await r2_service.upload_image(
        key=key,
        data=image_bytes,
        content_type=mime,
    )

    return {"image_url": image_url}


@router.post("/try-on")
async def try_on(
    request: Request,
    body: TryOnRequest,
    user: dict = Depends(require_auth),
):
    """Process a virtual try-on request. Accepts R2 URLs (tiny body)."""
    user_id = user.user_id
    db = get_db(request)
    vton_service = VtonService(request.app.state.env)
    r2_service = R2Service(request.app.state.env)

    product = await db.get_product(body.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product.image_url:
        raise HTTPException(status_code=400, detail="Product has no image available for try-on")

    vton_result = await db.create_vton_result({
        "user_id": user_id,
        "product_id": body.product_id,
        "status": "processing",
        "input_image_url": body.user_image_url,
        "garment_image_url": product.image_url,
    })

    result = await vton_service.process_try_on(
        user_image_url=body.user_image_url,
        garment_image_url=product.image_url,
        product_id=body.product_id,
        user_id=user_id,
    )

    if result["status"] == "failed":
        await db.update_vton_result(vton_result.id, {
            "status": "failed",
            "error_message": result.get("error", "VTON processing failed"),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        raise HTTPException(status_code=500, detail=result.get("error", "VTON processing failed"))

    image_bytes_result = result.get("image_bytes")
    if not image_bytes_result:
        await db.update_vton_result(vton_result.id, {
            "status": "failed",
            "error_message": "No image data returned from VTON model",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        raise HTTPException(status_code=500, detail="No image data returned from VTON model")

    content_type = result.get("content_type", "image/jpeg")

    output_image_url = await r2_service.upload_image(
        key=r2_service.generate_vton_key(user_id, body.product_id, is_result=True),
        data=image_bytes_result,
        content_type=content_type,
    )

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
