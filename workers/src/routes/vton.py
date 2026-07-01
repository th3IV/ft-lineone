"""Virtual Try-On routes."""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional

from models.vton_result import VtonResult, VtonStatus, VtonHistoryResponse
from services.vton import VtonService
from services.r2 import R2Service

router = APIRouter()


def get_db(request: Request):
    """Get database service from request state."""
    return request.app.state.db


@router.post("/try-on")
async def try_on(
    request: Request,
    user_image: UploadFile = File(...),
    product_id: str = Form(...),
):
    """Process a virtual try-on request."""
    # Validate file type
    if not user_image.content_type or not user_image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an image.",
        )

    # Validate file size (max 10MB)
    contents = await user_image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB.",
        )

    # Get user ID from auth middleware
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

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
    vton_result = VtonResult(
        user_id=user_id,
        product_id=product_id,
        status=VtonStatus.PROCESSING,
        input_image_url=user_image_url,
        garment_image_url=product.image_url,
    )

    # Process try-on
    result = await vton_service.process_try_on(
        user_image_bytes=contents,
        garment_image_url=product.image_url or "",
        product_id=product_id,
        user_id=user_id,
    )

    # Update result
    vton_result.status = VtonStatus(result["status"])
    if result.get("output_image_url"):
        vton_result.output_image_url = result["output_image_url"]
    if result.get("error"):
        vton_result.error_message = result["error"]

    return {
        "vton_id": vton_result.id,
        "status": vton_result.status.value,
        "input_image_url": vton_result.input_image_url,
        "output_image_url": vton_result.output_image_url,
    }


@router.get("/result/{vton_id}")
async def get_result(request: Request, vton_id: str):
    """Get the result of a VTON request."""
    # In a full implementation, this would query the database
    # For now, return a placeholder
    return {
        "id": vton_id,
        "status": "completed",
        "message": "VTON result retrieved successfully",
    }


@router.get("/history")
async def get_history(request: Request):
    """Get VTON history for the authenticated user."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # In a full implementation, this would query the database
    # For now, return empty history
    return VtonHistoryResponse(
        results=[],
        total=0,
    )
