"""Middleware for CORS, rate limiting, and authentication."""

import os
import time
from typing import Optional

from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from services.auth import verify_token


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old entries (older than 1 minute)
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                t for t in self.request_counts[client_ip]
                if current_time - t < 60
            ]
        else:
            self.request_counts[client_ip] = []

        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
            )

        # Record this request
        self.request_counts[client_ip].append(current_time)

        response = await call_next(request)
        return response


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for protected routes."""

    PROTECTED_PATHS = [
        "/api/v1/users/",
        "/api/v1/vton/",
        "/api/v1/recommendations/",
    ]

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public routes
        path = request.url.path
        is_protected = any(path.startswith(p) for p in self.PROTECTED_PATHS)

        if is_protected:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Missing or invalid authorization header",
                )

            token = auth_header.split(" ")[1]
            token_data = verify_token(token)

            if not token_data:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired token",
                )

            # Add user info to request state
            request.state.user_id = token_data.user_id
            request.state.user_email = token_data.email

        response = await call_next(request)
        return response


def setup_cors(app):
    """Configure CORS middleware."""
    cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
