from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.services.recommendation_service import RecommendationService
from app.application.services.user_service import UserService
from app.core.security import verify_token

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
recommendation_service = RecommendationService()
user_service = UserService()


async def get_current_user(authorization: str = Depends(lambda: None)) -> str:
    from fastapi import Header

    auth_header = Header(default="")
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("sub")


@router.get("")
async def get_recommendations(
    limit: int = Query(10, ge=1, le=50),
    user_id: str = Depends(get_current_user),
):
    try:
        user = await user_service.get_profile(user_id)
        products = await recommendation_service.get_recommendations(user, limit=limit)
        return {
            "user_id": user_id,
            "recommendations": [p.model_dump() for p in products],
            "count": len(products),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
