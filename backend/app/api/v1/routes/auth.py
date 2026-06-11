from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.application.services.user_service import UserService
from app.core.security import create_access_token, create_refresh_token, verify_token

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service():
    return UserService()


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register")
async def register(body: RegisterRequest):
    try:
        svc = get_user_service()
        user = await svc.register(body.name, body.email, body.password)
        access_token = create_access_token({"sub": user.id})
        refresh_token = create_refresh_token({"sub": user.id})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {"id": user.id, "name": user.name, "email": user.email},
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(body: LoginRequest):
    try:
        svc = get_user_service()
        user = await svc.login(body.email, body.password)
        access_token = create_access_token({"sub": user.id})
        refresh_token = create_refresh_token({"sub": user.id})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {"id": user.id, "name": user.name, "email": user.email},
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh")
async def refresh(body: RefreshRequest):
    payload = verify_token(body.refresh_token, expected_type="refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    new_access = create_access_token({"sub": user_id})
    new_refresh = create_refresh_token({"sub": user_id})
    return {"access_token": new_access, "refresh_token": new_refresh}
