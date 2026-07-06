"""Authentication routes."""

from fastapi import APIRouter, HTTPException, Request

from models.user import UserCreate, UserLogin, UserResponse, TokenResponse
from services.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password,
)
from services.database import DatabaseService

router = APIRouter()


def get_db(request: Request) -> DatabaseService:
    """Get database service from request state."""
    return request.app.state.db


def get_env(request: Request):
    """Get Workers env binding from request state."""
    return getattr(request.app.state, "env", None)


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, request: Request):
    """Register a new user."""
    db = get_db(request)
    env = get_env(request)

    existing_user = await db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await db.create_user({
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
    })

    access_token = create_access_token(user.id, user.email, env=env)
    refresh_token = create_refresh_token(user.id, user.email, env=env)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
            profile_image=user.profile_image,
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request):
    """Login with email and password."""
    db = get_db(request)
    env = get_env(request)

    user = await db.get_user_by_email(credentials.email)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(user.id, user.email, env=env)
    refresh_token = create_refresh_token(user.id, user.email, env=env)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
            body_measurements=user.body_measurements,
            preferences=user.preferences or {},
            profile_image=user.profile_image,
        ),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: dict, request: Request):
    """Refresh access token."""
    token = body.get("refresh_token", "")
    if not token:
        raise HTTPException(status_code=400, detail="refresh_token required")

    env = get_env(request)
    token_data = verify_token(token, expected_type="refresh", env=env)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    db = get_db(request)
    user = await db.get_user_by_id(token_data.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = create_access_token(user.id, user.email, env=env)
    new_refresh_token = create_refresh_token(user.id, user.email, env=env)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
            body_measurements=user.body_measurements,
            preferences=user.preferences or {},
            profile_image=user.profile_image,
        ),
    )
