from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.application.services.user_service import UserService
from app.core.security import verify_token

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service():
    return UserService()


async def get_current_user(authorization: str = Depends(lambda: None)) -> str:
    from fastapi import Header

    auth_header = Header(default="")
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("sub")


class MeasurementsRequest(BaseModel):
    body_measurements: dict


@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user)):
    try:
        svc = get_user_service()
        user = await svc.get_profile(user_id)
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "body_measurements": user.body_measurements,
            "preferences": user.preferences,
            "created_at": user.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/me/measurements")
async def update_measurements(
    body: MeasurementsRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        svc = get_user_service()
        user = await svc.update_measurements(user_id, body.body_measurements)
        return {"body_measurements": user.body_measurements}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/me/history")
async def get_history(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id, "history": []}
