"""Usage limit middleware for Freemium plan enforcement."""

from fastapi import Request, HTTPException
from datetime import datetime


async def require_usage(usage_type: str):
    """FastAPI dependency factory: check user hasn't exceeded daily limit."""
    async def _check(request: Request, user: dict):
        db = request.app.state.db
        user_id = user.user_id

        result = await db.can_use_feature(user_id, usage_type)

        if not result["allowed"]:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "usage_limit_exceeded",
                    "message": f"Límite diario de {usage_type.upper()} alcanzado ({result['current']}/{result['limit']})",
                    "current": result["current"],
                    "limit": result["limit"],
                    "upgrade_url": "/payment/upgrade",
                },
            )

        return result
    return _check


async def increment_and_check(request: Request, user: dict, usage_type: str):
    """Increment usage counter. Raises 402 if limit exceeded after increment."""
    db = request.app.state.db
    user_id = user.user_id
    today = datetime.utcnow().strftime("%Y-%m-%d")

    new_count = await db.increment_usage(user_id, usage_type, today)

    user_obj = await db.get_user_by_id(user_id)
    is_premium = getattr(user_obj, 'is_premium', False) or getattr(user_obj, 'plan_type', 'free') == 'premium'

    if not is_premium and new_count > 10:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "usage_limit_exceeded",
                "message": f"Límite diario de {usage_type.upper()} alcanzado ({new_count}/10)",
                "current": new_count,
                "limit": 10,
                "upgrade_url": "/payment/upgrade",
            },
        )

    return {"current": new_count, "limit": -1 if is_premium else 10}
