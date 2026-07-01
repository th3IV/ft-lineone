"""Authentication service for JWT tokens."""

import os
import hmac
import hashlib
import base64
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from pydantic import BaseModel


class TokenData(BaseModel):
    user_id: str
    email: str


def get_jwt_secret() -> str:
    """Get JWT secret from environment."""
    secret = os.getenv("JWT_SECRET")
    if not secret:
        secret = secrets.token_urlsafe(64)
        os.environ["JWT_SECRET"] = secret
    return secret


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _sign(payload: bytes, secret: str) -> str:
    return _b64url_encode(
        hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    )


def create_access_token(user_id: str, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=24))

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "type": "access",
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _sign(f"{header_b64}.{payload_b64}".encode(), get_jwt_secret())

    return f"{header_b64}.{payload_b64}.{signature}"


def create_refresh_token(user_id: str, email: str) -> str:
    """Create a JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=30)

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "type": "refresh",
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _sign(f"{header_b64}.{payload_b64}".encode(), get_jwt_secret())

    return f"{header_b64}.{payload_b64}.{signature}"


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature = parts
        expected_sig = _sign(f"{header_b64}.{payload_b64}".encode(), get_jwt_secret())

        if not hmac.compare_digest(signature, expected_sig):
            return None

        payload = json.loads(_b64url_decode(payload_b64))

        exp = payload.get("exp", 0)
        if datetime.now(timezone.utc).timestamp() > exp:
            return None

        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id and email:
            return TokenData(user_id=user_id, email=email)

    except Exception:
        pass
    return None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except Exception:
        return False
