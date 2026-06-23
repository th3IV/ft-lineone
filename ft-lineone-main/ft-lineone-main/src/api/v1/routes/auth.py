from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional

from src.application.use_cases.auth_use_cases import AuthUseCases
from src.core.security import decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()
auth_use_cases = AuthUseCases()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    body_measurements: Optional[dict] = None
    preferences: Optional[list[str]] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    body_measurements: Optional[dict] = None
    preferences: Optional[list[str]] = None


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_id


@router.post("/register")
async def register(request: RegisterRequest):
    try:
        result = await auth_use_cases.register(
            email=request.email,
            password=request.password,
            name=request.name,
            body_measurements=request.body_measurements,
            preferences=request.preferences,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login")
async def login(request: LoginRequest):
    try:
        result = await auth_use_cases.login(request.email, request.password)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        result = await auth_use_cases.logout(credentials.credentials)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user_id)):
    from src.infrastructure.external_services.supabase_client import SupabaseClient
    from src.infrastructure.database.postgres.repositories import UserRepository

    user_repo = UserRepository()
    user = await user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "body_measurements": user.get("body_measurements", {}),
        "preferences": user.get("preferences", []),
        "avatar_url": user.get("avatar_url", ""),
        "created_at": user.get("created_at"),
    }


@router.post("/refresh")
async def refresh(request: RefreshRequest):
    try:
        result = await auth_use_cases.refresh_tokens(request.refresh_token)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.patch("/profile")
async def update_profile(
    request: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        from src.infrastructure.external_services.supabase_client import SupabaseClient
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")
        result = await auth_use_cases.update_profile(
            access_token="",
            name=request.name,
            body_measurements=request.body_measurements,
            preferences=request.preferences,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))