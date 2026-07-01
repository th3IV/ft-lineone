"""Virtual Try-On routes."""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from typing import Optional

from models.vton_result import VtonResult, VtonStatus, VtonHistoryResponse
from services.vton import VtonService
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
    """Process a virtual try-on request."""
    # Validate file type
    if not user_image.content_type or not user_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    # Validate file size (max 10MB)
    contents = await user_image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    user_id = user.user_id
    db = get_db(request)
    vton_service = VtonService(request.app.state.env)
    r2_service = R2Service(request.app.state.env)

    # Get product details
    product = await db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Store user image in R2
    user_image_url = await r2_service.upload_image(
        key=r2_service.generate_vton_key(user_id, product_id, is_result=False),
        data=contents,
        content_type=user_image.content_type,
    )

    # Create VTON result record
    vton_result = await db.create_vton_result({
        "user_id": user_id,
        "product_id": product_id,
        "status": "processing",
        "input_image_url": user_image_url,
        "garment_image_url": product.image_url,
    })

    # Process try-on
    result = await vton_service.process_try_on(
        user_image_bytes=contents,
        garment_image_url=product.image_url or "",
        product_id=product_id,
        user_id=user_id,
    )

    return {
        "vton_id": vton_result.id,
        "status": result["status"],
        "input_image_url": user_image_url,
        "output_image_url": result.get("output_image_url"),
    }


@router.get("/result/{vton_id}")
async def get_result(request: Request, vton_id: str):
    """Get the result of a VTON request."""
    db = get_db(request)
    result = await db.get_vton_result(vton_id)
    if not result:
        raise HTTPException(status_code=404, detail="VTON result not found")

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
