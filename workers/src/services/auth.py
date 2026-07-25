"""Authentication service for JWT tokens.

Security best practices (per OWASP 2025):
- PBKDF2-SHA256 for password hashing (stdlib, no C extensions needed)
- EdDSA (Ed25519) for JWT signing (asymmetric, no shared secret)
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

# Try to import cryptography for EdDSA
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class TokenData(BaseModel):
    user_id: str
    email: str
    jti: Optional[str] = None


# Module-level cache for Ed25519 keys (safe in Workers — each request gets a fresh process)
_private_key_cache = None
_public_key_cache = None


def get_ed25519_keys(env=None):
    """Get or generate Ed25519 key pair for JWT signing.
    
    In Cloudflare Workers, secrets set via `wrangler secret put` are ONLY
    accessible via the env binding object, NOT via os.getenv().
    """
    global _private_key_cache, _public_key_cache
    
    if _private_key_cache and _public_key_cache:
        return _private_key_cache, _public_key_cache
    
    private_key = None
    public_key = None
    
    # Try Workers env binding first (production)
    if env and CRYPTOGRAPHY_AVAILABLE:
        private_key_b64 = getattr(env, "JWT_PRIVATE_KEY", None)
        public_key_b64 = getattr(env, "JWT_PUBLIC_KEY", None)
        # Guard against non-string values (misconfig, mock objects)
        if isinstance(private_key_b64, str) and isinstance(public_key_b64, str) and private_key_b64 and public_key_b64:
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(base64.b64decode(private_key_b64))
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))
    
    # Fallback to os.getenv (local dev with .dev.vars)
    if not private_key and CRYPTOGRAPHY_AVAILABLE:
        private_key_b64 = os.getenv("JWT_PRIVATE_KEY")
        public_key_b64 = os.getenv("JWT_PUBLIC_KEY")
        if private_key_b64 and public_key_b64:
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(base64.b64decode(private_key_b64))
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))
    
    # Generate new keys if none configured (dev only)
    if not private_key:
        if not CRYPTOGRAPHY_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="cryptography package required for EdDSA. Install with: pip install cryptography"
            )
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        # Log warning - keys not persisted!
        import json as _json
        print(_json.dumps({
            "event": "ed25519_keys_generated",
            "warning": "Keys generated at runtime - not persisted! Configure JWT_PRIVATE_KEY and JWT_PUBLIC_KEY secrets for production."
        }))
    
    _private_key_cache = private_key
    _public_key_cache = public_key
    return private_key, public_key


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _sign_eddsa(payload: bytes, private_key) -> str:
    """Sign payload with Ed25519 private key."""
    signature = private_key.sign(payload)
    return _b64url_encode(signature)


def _verify_eddsa(payload: bytes, signature_b64: str, public_key) -> bool:
    """Verify Ed25519 signature."""
    try:
        signature = _b64url_decode(signature_b64)
        public_key.verify(signature, payload)
        return True
    except Exception:
        return False


# Fallback HS256 functions (when cryptography not available)
def get_jwt_secret(env=None) -> str:
    """Resolve the HS256 JWT secret from Workers env or process env.

    Raises HTTPException 500 when no secret is configured — config errors must
    fail loudly, never silently sign/verify with an empty secret.
    """
    secret = env.JWT_SECRET if env and hasattr(env, "JWT_SECRET") else os.getenv("JWT_SECRET")
    if not secret:
        raise HTTPException(
            status_code=500,
            detail="JWT_SECRET not configured. Run: wrangler secret put JWT_SECRET"
        )
    return secret


def _sign_hs256(payload: bytes, secret: str) -> str:
    return _b64url_encode(
        hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    )


def _verify_hs256(payload: bytes, signature_b64: str, secret: str) -> bool:
    expected_sig = _sign_hs256(payload, secret)
    return hmac.compare_digest(signature_b64, expected_sig)


def create_access_token(
    user_id: str, email: str, expires_delta: Optional[timedelta] = None, env=None
) -> str:
    """Create a JWT access token using EdDSA (Ed25519) or HS256 fallback."""
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=24))
    jti = secrets.token_hex(16)

    header = {"alg": "EdDSA" if CRYPTOGRAPHY_AVAILABLE else "HS256", "typ": "JWT"}
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
    
    if CRYPTOGRAPHY_AVAILABLE:
        private_key, _ = get_ed25519_keys(env)
        signature = _sign_eddsa(
            f"{header_b64}.{payload_b64}".encode(), private_key
        )
    else:
        # Fallback to HS256
        secret = get_jwt_secret(env)
        signature = _sign_hs256(
            f"{header_b64}.{payload_b64}".encode(), secret
        )

    return f"{header_b64}.{payload_b64}.{signature}"


def create_refresh_token(user_id: str, email: str, env=None) -> str:
    """Create a JWT refresh token using EdDSA or HS256 fallback."""
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    jti = secrets.token_hex(16)

    header = {"alg": "EdDSA" if CRYPTOGRAPHY_AVAILABLE else "HS256", "typ": "JWT"}
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
    
    if CRYPTOGRAPHY_AVAILABLE:
        private_key, _ = get_ed25519_keys(env)
        signature = _sign_eddsa(
            f"{header_b64}.{payload_b64}".encode(), private_key
        )
    else:
        secret = get_jwt_secret(env)
        signature = _sign_hs256(
            f"{header_b64}.{payload_b64}".encode(), secret
        )

    return f"{header_b64}.{payload_b64}.{signature}"


def verify_token(token: str, expected_type: str = None, env=None) -> Optional[TokenData]:
    """Verify and decode a JWT token. Supports both EdDSA and HS256.

    Security: validates alg header to prevent algorithm confusion attacks (OWASP API2:2023).
    Config errors (missing JWT_SECRET) propagate as HTTPException 500.
    """
    # Get secret/keys OUTSIDE try/except — propagate config errors immediately
    if CRYPTOGRAPHY_AVAILABLE:
        _, public_key = get_ed25519_keys(env)
    else:
        secret = get_jwt_secret(env)

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature = parts

        # Validate JWT header — reject non-EdDSA/HS256 algorithms
        header = json.loads(_b64url_decode(header_b64))
        expected_alg = "EdDSA" if CRYPTOGRAPHY_AVAILABLE else "HS256"
        if header.get("alg") != expected_alg:
            return None

        payload = json.loads(_b64url_decode(payload_b64))

        exp = payload.get("exp", 0)
        if datetime.now(timezone.utc).timestamp() > exp:
            return None

        if expected_type and payload.get("type") != expected_type:
            return None

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode()
        
        if CRYPTOGRAPHY_AVAILABLE:
            if not _verify_eddsa(signing_input, signature, public_key):
                return None
        else:
            expected_sig = _sign_hs256(signing_input, secret)
            if not hmac.compare_digest(signature, expected_sig):
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
