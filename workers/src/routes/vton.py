"""Virtual Try-On routes."""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from fastapi.responses import Response
from typing import Optional

from models.vton_result import VtonResult, VtonStatus, VtonHistoryResponse
from services.vton import VtonService, _validate_image
from services.r2 import R2Service
from middleware.security import require_auth

router = APIRouter()


def get_db(request: Request):
    """Get database service from request state."""
    return request.app.state.db


@router.post("/try-on")
async def try_on(
    request: Request,
    user_image: UploadFile = File(...),
    product_id: str = Form(...),
    user: dict = Depends(require_auth),
):
    """Process a virtual try-on request. Returns the result image directly as JPEG."""
    if not user_image.content_type or not user_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    contents = await user_image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    if not _validate_image(contents):
        raise HTTPException(status_code=400, detail="Invalid image format. Please upload a JPEG, PNG, or WebP file.")

    user_id = user.user_id
    db = get_db(request)
    vton_service = VtonService(request.app.state.env)
    r2_service = R2Service(request.app.state.env)

    product = await db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product.image_url:
        raise HTTPException(status_code=400, detail="Product has no image available for try-on")

    user_image_url = await r2_service.upload_image(
        key=r2_service.generate_vton_key(user_id, product_id, is_result=False),
        data=contents,
        content_type=user_image.content_type or "image/jpeg",
    )

    vton_result = await db.create_vton_result({
        "user_id": user_id,
        "product_id": product_id,
        "status": "processing",
        "input_image_url": user_image_url,
        "garment_image_url": product.image_url,
    })

    result = await vton_service.process_try_on(
        user_image_url=user_image_url,
        garment_image_url=product.image_url,
        product_id=product_id,
        user_id=user_id,
    )

    from datetime import datetime, timezone
    await db.update_vton_result(vton_result.id, {
        "status": result["status"],
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })

    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail=result.get("error", "VTON processing failed"))

    image_bytes = result.get("image_bytes")
    if not image_bytes:
        raise HTTPException(status_code=500, detail="No image data returned from VTON model")

    content_type = result.get("content_type", "image/jpeg")
    return Response(content=image_bytes, media_type=content_type)


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
