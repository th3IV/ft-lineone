"""Authentication routes."""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import EmailStr

from models.user import UserCreate, UserLogin, UserResponse, TokenResponse, UserUpdate
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


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, request: Request):
    """Register a new user."""
    db = get_db(request)

    # Check if user already exists
    existing_user = await db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    # Create user
    user = await db.create_user({
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
    })

    # Generate tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request):
    """Login with email and password."""
    db = get_db(request)

    user = await db.get_user_by_email(credentials.email)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # Generate tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
            body_measurements=user.body_measurements,
            preferences=user.preferences or [],
        ),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, request: Request):
    """Refresh access token."""
    token_data = verify_token(refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
        )

    db = get_db(request)
    user = await db.get_user_by_email(token_data.email)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    # Generate new tokens
    new_access_token = create_access_token(user.id, user.email)
    new_refresh_token = create_refresh_token(user.id, user.email)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
        ),
    )
