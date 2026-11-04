"""Middleware for CORS, rate limiting, authentication, and request tracing."""

import json
import time
from fastapi import Request, HTTPException

from services.auth import verify_token, is_token_revoked


def _is_production(request: Request) -> bool:
    """Check if running in production via Workers env binding (not os.getenv)."""
    env = getattr(request.app.state, "env", None)
    if env:
        return getattr(env, "ENVIRONMENT", "development") == "production"
    return False


def safe_error_message(e: Exception, request: Request = None) -> str:
    """Return a user-safe error message. In production, internal details are hidden."""
    if request and _is_production(request):
        return "An internal error occurred. Please try again."
    return str(e)


def generate_request_id() -> str:
    """Generate a cryptographically secure request ID."""
    import hashlib
    import secrets
    return hashlib.sha256(secrets.token_bytes(16)).hexdigest()[:16]


class AuthMiddleware:
    """Authentication middleware for protected routes.

    Applied per-route via Depends() rather than as global middleware,
    since Workers are stateless and in-memory rate limiting doesn't persist.
    """

    PROTECTED_PATHS = [
        "/api/v1/users/",
        "/api/v1/vton/",
        "/api/v1/recommendations/",
    ]

    @staticmethod
    def is_protected(path: str) -> bool:
        return any(path.startswith(p) for p in AuthMiddleware.PROTECTED_PATHS)

    @staticmethod
    def extract_user(request: Request) -> dict | None:
        """Extract and verify user from Authorization header."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        env = getattr(request.app.state, "env", None)
        return verify_token(token, env=env)


async def require_auth(request: Request) -> dict:
    """FastAPI dependency: require authenticated user.

    Checks JWT signature, expiry, and revocation status.
    """
    user = AuthMiddleware.extract_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    db = getattr(request.app.state, "db", None)
    if user.jti and await is_token_revoked(user.jti, db):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    return user


async def require_admin(request: Request) -> dict:
    """FastAPI dependency: require admin user.

    Currently uses a simple email-based admin list from env var ADMIN_EMAILS.
    In production, this should use a proper role field in the users table.
    """
    user = await require_auth(request)
    env = getattr(request.app.state, "env", None)
    admin_emails_str = getattr(env, "ADMIN_EMAILS", "") if env else ""
    admin_emails = [e.strip().lower() for e in admin_emails_str.split(",") if e.strip()]

    if not admin_emails or user.email.lower() not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


async def optional_auth(request: Request) -> dict | None:
    """FastAPI dependency: optionally extract user."""
    return AuthMiddleware.extract_user(request)
