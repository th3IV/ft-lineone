"""Authentication routes."""

from fastapi import APIRouter, HTTPException, Request

from models.user import UserCreate, UserLogin, UserResponse, TokenResponse
from services.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password,
    check_rate_limit,
    record_login_attempt,
    revoke_token,
    is_token_revoked,
)
from services.database import DatabaseService
from services.config import VTON_DAILY_LIMIT_FREE
from datetime import datetime, timezone

router = APIRouter()


def get_db(request: Request) -> DatabaseService:
    """Get database service from request state."""
    return request.app.state.db


def get_env(request: Request):
    """Get Workers env binding from request state."""
    return getattr(request.app.state, "env", None)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers."""
    forwarded = request.headers.get("cf-connecting-ip", "")
    if forwarded:
        return forwarded
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return "unknown"


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, request: Request):
    """Register a new user. Rate limited by IP."""
    db = get_db(request)
    env = get_env(request)
    ip = get_client_ip(request)

    allowed = await check_rate_limit(f"register:{ip}", db, max_attempts=5, window_minutes=60)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many registration attempts. Try again later.")

    existing_user = await db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_data_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
    }
    if user_data.age is not None:
        user_data_dict["age"] = user_data.age
    if user_data.gender is not None:
        user_data_dict["body_measurements"] = {"gender": user_data.gender}

    user = await db.create_user(user_data_dict)

    await record_login_attempt(f"register:{ip}", ip, True, db)

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
            is_premium=user.is_premium,
            plan_type=getattr(user, 'plan_type', 'free'),
            daily_usage={"vton": 0, "llm": 0, "limit": VTON_DAILY_LIMIT_FREE, "plan_type": "free"},
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request):
    """Login with email and password. Rate limited by email and IP."""
    db = get_db(request)
    env = get_env(request)
    ip = get_client_ip(request)

    allowed_email = await check_rate_limit(f"login:{credentials.email}", db, max_attempts=10, window_minutes=15)
    allowed_ip = await check_rate_limit(f"login:{ip}", db, max_attempts=20, window_minutes=15)
    if not allowed_email or not allowed_ip:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 15 minutes.")

    user = await db.get_user_by_email(credentials.email)
    success = user is not None and verify_password(credentials.password, user.password_hash if user else "")

    await record_login_attempt(f"login:{credentials.email}", ip, success, db)

    if not success:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(user.id, user.email, env=env)
    refresh_token = create_refresh_token(user.id, user.email, env=env)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    is_premium = user.is_premium or getattr(user, 'plan_type', 'free') == 'premium'
    usage = await db.get_user_usage_readonly(user.id, today)

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
            is_premium=user.is_premium,
            plan_type=getattr(user, 'plan_type', 'free'),
            daily_usage={
                "vton": usage["vton_count"],
                "llm": usage["llm_count"],
                "limit": -1 if is_premium else 5,
                "plan_type": getattr(user, 'plan_type', 'free'),
            },
        ),
    )


@router.post("/logout")
async def logout(request: Request):
    """Logout by revoking the current access and refresh tokens.

    Accepts the access token via Authorization header and optionally
    the refresh token in the request body.
    """
    import json as _json
    import base64

    env = get_env(request)
    db = get_db(request)

    revoked_any = False

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        token_data = verify_token(token, env=env)
        if token_data and token_data.jti:
            payload_parts = token.split(".")
            if len(payload_parts) == 3:
                payload_b64 = payload_parts[1]
                payload_b64 += "=" * (4 - len(payload_b64) % 4)
                payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
                exp = payload.get("exp", 0)
                await revoke_token(token_data.jti, token_data.user_id, exp, db)
                revoked_any = True

    try:
        body = await request.json()
        refresh_token_str = body.get("refresh_token", "")
        if refresh_token_str:
            refresh_data = verify_token(refresh_token_str, expected_type="refresh", env=env)
            if refresh_data and refresh_data.jti:
                payload_parts = refresh_token_str.split(".")
                if len(payload_parts) == 3:
                    payload_b64 = payload_parts[1]
                    payload_b64 += "=" * (4 - len(payload_b64) % 4)
                    payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
                    exp = payload.get("exp", 0)
                    await revoke_token(refresh_data.jti, refresh_data.user_id, exp, db)
                    revoked_any = True
    except Exception:
        pass

    return {"status": "ok", "detail": "Logged out successfully", "revoked": revoked_any}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: dict, request: Request):
    """Refresh access token."""
    token = body.get("refresh_token", "")
    if not token:
        raise HTTPException(status_code=400, detail="refresh_token required")

    env = get_env(request)
    db = get_db(request)

    token_data = verify_token(token, expected_type="refresh", env=env)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    from services.auth import is_token_revoked
    if token_data.jti and await is_token_revoked(token_data.jti, db):
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    user = await db.get_user_by_id(token_data.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if token_data.jti:
        import base64
        payload_parts = token.split(".")
        if len(payload_parts) == 3:
            payload_b64 = payload_parts[1]
            payload_b64 += "=" * (4 - len(payload_b64) % 4)
            import json as _json
            payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
            exp = payload.get("exp", 0)
            await revoke_token(token_data.jti, token_data.user_id, exp, db)

    new_access_token = create_access_token(user.id, user.email, env=env)
    new_refresh_token = create_refresh_token(user.id, user.email, env=env)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    is_premium = user.is_premium or getattr(user, 'plan_type', 'free') == 'premium'
    usage = await db.get_user_usage_readonly(user.id, today)

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
            is_premium=user.is_premium,
            plan_type=getattr(user, 'plan_type', 'free'),
            daily_usage={
                "vton": usage["vton_count"],
                "llm": usage["llm_count"],
                "limit": -1 if is_premium else 5,
                "plan_type": getattr(user, 'plan_type', 'free'),
            },
        ),
    )
