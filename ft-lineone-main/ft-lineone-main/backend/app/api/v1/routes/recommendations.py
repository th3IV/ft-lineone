from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.application.services.recommendation_service import RecommendationService
from app.application.services.user_service import UserService
from app.core.security import verify_token

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_recommendation_service():
    return RecommendationService()


def get_user_service():
    return UserService()


async def get_current_user(authorization: str = Header("")) -> str:
    token = authorization.replace("Bearer ", "")
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
        svc = get_recommendation_service()
        user_svc = get_user_service()
        user = await user_svc.get_profile(user_id)
        products = await svc.get_recommendations(user, limit=limit)
        return {
            "user_id": user_id,
            "recommendations": [p.model_dump() for p in products],
            "count": len(products),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
