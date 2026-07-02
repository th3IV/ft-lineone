"""Authentication service for JWT tokens.

Security best practices (per OWASP 2025):
- PBKDF2-SHA256 for password hashing (stdlib, no C extensions needed)
- HMAC-SHA256 for JWT signing (stdlib)
- Timing-safe comparison via hmac.compare_digest
- Secrets never hardcoded, accessed via Workers env binding
"""

import os
import hmac
import hashlib
import base64
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel


class TokenData(BaseModel):
    user_id: str
    email: str


# Module-level cache for JWT secret (safe in Workers — each request gets a fresh process)
_jwt_secret_cache: Optional[str] = None


def get_jwt_secret(env=None) -> str:
    """Get JWT secret from Workers env binding or environment variable.

    In Cloudflare Workers, secrets set via `wrangler secret put` are ONLY
    accessible via the env binding object, NOT via os.getenv().
    """
    global _jwt_secret_cache
    if _jwt_secret_cache:
        return _jwt_secret_cache

    secret = None
    # Try Workers env binding first (production)
    if env:
        secret = getattr(env, "JWT_SECRET", None)
    # Fallback to os.getenv (local dev with .dev.vars)
    if not secret:
        secret = os.getenv("JWT_SECRET")
    if not secret:
        raise HTTPException(
            status_code=500,
            detail="JWT_SECRET not configured. Run: wrangler secret put JWT_SECRET",
        )
    _jwt_secret_cache = secret
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


def create_access_token(
    user_id: str, email: str, expires_delta: Optional[timedelta] = None, env=None
) -> str:
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
    signature = _sign(
        f"{header_b64}.{payload_b64}".encode(), get_jwt_secret(env)
    )

    return f"{header_b64}.{payload_b64}.{signature}"


def create_refresh_token(user_id: str, email: str, env=None) -> str:
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
    signature = _sign(
        f"{header_b64}.{payload_b64}".encode(), get_jwt_secret(env)
    )

    return f"{header_b64}.{payload_b64}.{signature}"


def verify_token(token: str, expected_type: str = None, env=None) -> Optional[TokenData]:
    """Verify and decode a JWT token. Optionally check token type."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature = parts
        expected_sig = _sign(
            f"{header_b64}.{payload_b64}".encode(), get_jwt_secret(env)
        )

        if not hmac.compare_digest(signature, expected_sig):
            return None

        payload = json.loads(_b64url_decode(payload_b64))

        exp = payload.get("exp", 0)
        if datetime.now(timezone.utc).timestamp() > exp:
            return None

        if expected_type and payload.get("type") != expected_type:
            return None

        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id and email:
            return TokenData(user_id=user_id, email=email)

    except Exception:
        pass
    return None


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-SHA256 (stdlib, no C extensions).

    Uses 260,000 iterations (OWASP 2025 recommendation for PBKDF2-SHA256).
    Salt is generated via secrets.token_bytes (cryptographically secure).
    Format: iterations:salt_hex:hash_hex
    """
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260000)
    return f"260000:{salt.hex()}:{dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its PBKDF2-SHA256 hash.

    Supports both new PBKDF2 format (260000:salt:hash) and legacy bcrypt format
    for backward compatibility during migration.
    """
    try:
        if hashed_password.startswith("260000:"):
            # New PBKDF2 format
            parts = hashed_password.split(":")
            iterations = int(parts[0])
            salt = bytes.fromhex(parts[1])
            stored_hash = bytes.fromhex(parts[2])
            dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt, iterations)
            return hmac.compare_digest(dk, stored_hash)
        else:
            # Legacy bcrypt hash — cannot verify without bcrypt, return False
            # Users with bcrypt hashes will need to reset password
            return False
    except Exception:
        return False
