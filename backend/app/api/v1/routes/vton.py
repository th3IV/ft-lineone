from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form

from app.application.services.vton_service import VTONService
from app.core.security import verify_token

router = APIRouter(prefix="/vton", tags=["vton"])


def get_vton_service():
    return VTONService()


async def get_current_user(authorization: str = Header("")) -> str:
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("sub")


@router.post("/try-on")
async def try_on(
    product_id: str = Form(...),
    user_id: str = Depends(get_current_user),
    user_image: UploadFile | None = File(None),
    user_image_url: str = Form(""),
):
    svc = get_vton_service()
    if user_image_url:
        image_url = user_image_url
    elif user_image:
        image_url = f"uploads/{user_id}/{user_image.filename}"
    else:
        raise HTTPException(status_code=400, detail="Provide user_image (file) or user_image_url")
    try:
        result = await svc.request_try_on(user_id, product_id, image_url)
        return {
            "vton_id": result.id,
            "status": result.status.value,
            "input_image_url": result.input_image_url,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/result/{vton_id}")
async def get_vton_result(vton_id: str, user_id: str = Depends(get_current_user)):
    svc = get_vton_service()
    result = await svc.get_result(vton_id)
    if not result:
        raise HTTPException(status_code=404, detail="VTON result not found")
    return {
        "id": result.id,
        "status": result.status.value,
        "input_image_url": result.input_image_url,
        "output_image_url": result.output_image_url,
        "created_at": result.created_at.isoformat(),
    }
