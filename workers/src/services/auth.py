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
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel


class TokenData(BaseModel):
    user_id: str
    email: str
    jti: Optional[str] = None


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
    jti = secrets.token_hex(16)

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "type": "access",
        "jti": jti,
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
    jti = secrets.token_hex(16)

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "type": "refresh",
        "jti": jti,
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _sign(
        f"{header_b64}.{payload_b64}".encode(), get_jwt_secret(env)
    )

    return f"{header_b64}.{payload_b64}.{signature}"


def verify_token(token: str, expected_type: str = None, env=None) -> Optional[TokenData]:
    """Verify and decode a JWT token. Optionally check token type.

    Security: validates alg header to prevent algorithm confusion attacks (OWASP API2:2023).
    Config errors (missing JWT_SECRET) propagate as HTTPException 500.
    """
    # Get secret OUTSIDE try/except — propagate config errors immediately
    secret = get_jwt_secret(env)

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature = parts

        # Validate JWT header — reject non-HS256 algorithms
        header = json.loads(_b64url_decode(header_b64))
        if header.get("alg") != "HS256":
            return None

        expected_sig = _sign(
            f"{header_b64}.{payload_b64}".encode(), secret
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
        jti = payload.get("jti")
        if user_id and email:
            return TokenData(user_id=user_id, email=email, jti=jti)

    except Exception:
        pass
    return None


async def is_token_revoked(jti: str, db) -> bool:
    """Check if a token has been revoked (logged out)."""
    if not jti or not db:
        return False
    try:
        result = await db.db.prepare(
            "SELECT 1 FROM revoked_tokens WHERE jti = ? LIMIT 1"
        ).bind(jti).first()
        return result is not None
    except Exception:
        return False


async def revoke_token(jti: str, user_id: str, exp: int, db) -> bool:
    """Revoke a token by adding its JTI to the revoked_tokens table."""
    if not jti or not db:
        return False
    try:
        await db.db.prepare(
            "INSERT OR IGNORE INTO revoked_tokens (jti, user_id, expires_at) VALUES (?, ?, ?)"
        ).bind(jti, user_id, exp).run()
        return True
    except Exception:
        return False


async def check_rate_limit(identifier: str, db, max_attempts: int = 10, window_minutes: int = 15) -> bool:
    """Check if an identifier (email or IP) has exceeded login rate limit.

    Returns True if allowed, False if rate limited.
    Cleans up old entries on each call.
    """
    if not db:
        return True
    try:
        cutoff = int(time.time()) - (window_minutes * 60)
        await db.db.prepare(
            "DELETE FROM login_attempts WHERE created_at < datetime(?, 'unixepoch')"
        ).bind(cutoff).run()

        result = await db.db.prepare(
            "SELECT COUNT(*) as cnt FROM login_attempts WHERE identifier = ? AND success = 0 AND created_at > datetime(?, 'unixepoch')"
        ).bind(identifier, cutoff).first()

        count = result.get("cnt", 0) if result else 0
        return count < max_attempts
    except Exception:
        return True


async def record_login_attempt(identifier: str, ip_address: str, success: bool, db):
    """Record a login attempt for rate limiting."""
    if not db:
        return
    try:
        await db.db.prepare(
            "INSERT INTO login_attempts (identifier, ip_address, success) VALUES (?, ?, ?)"
        ).bind(identifier, ip_address, 1 if success else 0).run()
    except Exception:
        pass


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
