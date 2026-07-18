"""Usage limit middleware for Freemium plan enforcement."""

from fastapi import Request, HTTPException
from datetime import datetime, timezone

from services.config import (
    VTON_DAILY_LIMIT_FREE,
    LLM_DAILY_LIMIT_FREE,
)


_LIMITS = {
    "vton": VTON_DAILY_LIMIT_FREE,
    "llm": LLM_DAILY_LIMIT_FREE,
}


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
    """Atomic check-and-increment. Raises 402 if limit would be exceeded.

    Uses try_increment_usage() which performs a conditional UPDATE in a single
    statement to avoid TOCTOU race conditions.
    """
    db = request.app.state.db
    user_id = user.user_id
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    user_obj = await db.get_user_by_id(user_id)
    is_premium = getattr(user_obj, 'is_premium', False) or getattr(user_obj, 'plan_type', 'free') == 'premium'

    free_limit = _LIMITS.get(usage_type, VTON_DAILY_LIMIT_FREE)
    effective_limit = -1 if is_premium else free_limit

    result = await db.try_increment_usage(user_id, usage_type, today, effective_limit)

    if not result["allowed"]:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "usage_limit_exceeded",
                "message": f"Límite diario de {usage_type.upper()} alcanzado ({free_limit}/{free_limit})",
                "current": free_limit,
                "limit": free_limit,
                "upgrade_url": "/payment/upgrade",
            },
        )

    return {"current": result["new_count"], "limit": effective_limit}
