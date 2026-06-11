from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from app.application.services.vton_service import VTONService
from app.core.security import verify_token

router = APIRouter(prefix="/vton", tags=["vton"])
vton_service = VTONService()


async def get_current_user(authorization: str = Depends(lambda: None)) -> str:
    from fastapi import Header

    auth_header = Header(default="")
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("sub")


@router.post("/try-on")
async def try_on(
    product_id: str = Form(...),
    user_image: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    image_url = f"uploads/{user_id}/{user_image.filename}"
    try:
        result = await vton_service.request_try_on(user_id, product_id, image_url)
        return {
            "vton_id": result.id,
            "status": result.status.value,
            "input_image_url": result.input_image_url,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/result/{vton_id}")
async def get_vton_result(vton_id: str, user_id: str = Depends(get_current_user)):
    result = await vton_service.get_result(vton_id)
    if not result:
        raise HTTPException(status_code=404, detail="VTON result not found")
    return {
        "id": result.id,
        "status": result.status.value,
        "input_image_url": result.input_image_url,
        "output_image_url": result.output_image_url,
        "created_at": result.created_at.isoformat(),
    }
