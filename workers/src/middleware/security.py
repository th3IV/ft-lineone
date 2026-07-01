"""Middleware for CORS, rate limiting, and authentication."""

from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from services.auth import verify_token


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
        return verify_token(token)


async def require_auth(request: Request) -> dict:
    """FastAPI dependency: require authenticated user."""
    user = AuthMiddleware.extract_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def optional_auth(request: Request) -> dict | None:
    """FastAPI dependency: optionally extract user."""
    return AuthMiddleware.extract_user(request)
