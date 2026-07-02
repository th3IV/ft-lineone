"""User profile routes."""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional

from middleware.security import require_auth

router = APIRouter()


def get_db(request: Request):
    """Get database service from request state."""
    return request.app.state.db


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None


class MeasurementsUpdate(BaseModel):
    height: Optional[float] = None
    weight: Optional[float] = None
    chest: Optional[float] = None
    waist: Optional[float] = None
    hips: Optional[float] = None
    bodyShape: Optional[str] = None


class PreferencesUpdate(BaseModel):
    preferences: dict = {}


@router.get("/me")
async def get_current_user(request: Request, user: dict = Depends(require_auth)):
    """Get current user profile with measurements and preferences."""
    db = get_db(request)
    user_obj = await db.get_user_by_id(user.user_id)
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    measurements = user_obj.body_measurements or {}
    gender = measurements.get("gender", "")

    return {
        "id": user_obj.id,
        "email": user_obj.email,
        "name": user_obj.name,
        "gender": gender,
        "created_at": user_obj.created_at,
        "body_measurements": measurements,
        "preferences": user_obj.preferences or {},
    }


@router.put("/profile")
async def update_profile(
    body: ProfileUpdate,
    request: Request,
    user: dict = Depends(require_auth),
):
    """Update user profile (name, email, gender)."""
    db = get_db(request)
    updates = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.email is not None:
        updates["email"] = body.email
    if body.gender is not None:
        user_obj = await db.get_user_by_id(user.user_id)
        measurements = user_obj.body_measurements or {}
        measurements["gender"] = body.gender
        updates["body_measurements"] = measurements

    if updates:
        await db.update_user(user.user_id, updates)

    return {"status": "updated", "fields": list(updates.keys())}


@router.put("/measurements")
async def update_measurements(
    body: MeasurementsUpdate,
    request: Request,
    user: dict = Depends(require_auth),
):
    """Update user body measurements."""
    db = get_db(request)
    measurements = {k: v for k, v in body.model_dump().items() if v is not None}
    await db.update_user(user.user_id, {"body_measurements": measurements})
    return {"status": "updated", "measurements": measurements}


@router.put("/preferences")
async def update_preferences(
    body: PreferencesUpdate,
    request: Request,
    user: dict = Depends(require_auth),
):
    """Update user style preferences."""
    db = get_db(request)
    await db.update_user(user.user_id, {"preferences": body.preferences})
    return {"status": "updated", "preferences": body.preferences}
