"""User profile routes."""

import base64
import re
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional

from middleware.security import require_auth
from services.r2 import upload_profile_image

router = APIRouter()


def get_db(request: Request):
    """Get database service from request state."""
    return request.app.state.db


def get_env(request: Request):
    """Get Workers env binding from request state."""
    return getattr(request.app.state, "env", None)


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None


class MeasurementsUpdate(BaseModel):
    height: Optional[float] = None
    weight: Optional[float] = None
    chest: Optional[float] = None
    waist: Optional[float] = None
    hips: Optional[float] = None
    bodyShape: Optional[str] = None


class PreferencesUpdate(BaseModel):
    preferences: dict = {}


class ProfileImageUpdate(BaseModel):
    image_base64: str


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
        "profile_image": user_obj.profile_image,
        "is_premium": user_obj.is_premium,
        "age": user_obj.age,
    }


@router.put("/profile")
async def update_profile(
    body: ProfileUpdate,
    request: Request,
    user: dict = Depends(require_auth),
):
    """Update user profile (name, email, gender, age)."""
    db = get_db(request)
    updates = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.email is not None:
        updates["email"] = body.email
    if body.age is not None:
        updates["age"] = body.age
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
    user_obj = await db.get_user_by_id(user.user_id)
    existing = user_obj.body_measurements if user_obj else {}
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    merged = {**(existing or {}), **updates}
    await db.update_user(user.user_id, {"body_measurements": merged})
    return {"status": "updated", "measurements": merged}


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


@router.post("/profile-image")
async def upload_profile_image_route(
    body: ProfileImageUpdate,
    request: Request,
    user: dict = Depends(require_auth),
):
    """Upload a user profile image (base64) to R2 and update the user record."""
    env = get_env(request)
    if not env or not getattr(env, "BUCKET", None):
        raise HTTPException(status_code=500, detail="R2 bucket not configured")

    # Extract data URI prefix and bytes
    data = body.image_base64
    content_type = "image/jpeg"
    if "," in data:
        header, b64data = data.split(",", 1)
        mime_match = re.match(r"data:([a-zA-Z0-9/+-]+);base64", header)
        if mime_match:
            content_type = mime_match.group(1)
    else:
        b64data = data

    try:
        image_bytes = base64.b64decode(b64data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    if len(image_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 5MB)")

    try:
        public_url = await upload_profile_image(env, user.user_id, image_bytes, content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

    db = get_db(request)
    await db.update_user(user.user_id, {"profile_image": public_url})

    return {"status": "updated", "profile_image": public_url}


@router.delete("/profile-image")
async def delete_profile_image(
    request: Request,
    user: dict = Depends(require_auth),
):
    """Delete user profile image."""
    db = get_db(request)
    await db.update_user(user.user_id, {"profile_image": None})
    return {"status": "deleted"}


class PremiumUpdate(BaseModel):
    is_premium: bool


@router.patch("/{user_id}/premium")
async def set_premium(
    user_id: str,
    body: PremiumUpdate,
    request: Request,
):
    """Toggle premium status for a user. Requires X-Admin-Key header."""
    env = get_env(request)
    admin_key = getattr(env, "ADMIN_KEY", None) if env else None
    if not admin_key:
        raise HTTPException(status_code=500, detail="ADMIN_KEY not configured")

    header_key = request.headers.get("X-Admin-Key", "")
    if header_key != admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    db = get_db(request)
    success = await db.set_premium_status(user_id, body.is_premium)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or no changes")

    return {"status": "updated", "is_premium": body.is_premium}
