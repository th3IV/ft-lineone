import json
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from routes import auth, products, vton, recommendations, scrapers

app = FastAPI(
    title="FT-LineOne API",
    description="Fashion Try-On Platform API - Cloudflare Workers",
    version="2.0.0",
)

# CORS middleware - configured via env vars
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(vton.router, prefix="/api/v1/vton", tags=["VTON"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])
app.include_router(scrapers.router, prefix="/api/v1/scrapers", tags=["Scrapers"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0", "runtime": "cloudflare-workers"}


@app.get("/")
async def root():
    return {
        "service": "ft-lineone-api",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Cloudflare Workers ASGI entry point
async def on_fetch(request: Request, env: Any, ctx: Any) -> Response:
    """Cloudflare Workers Python entry point."""
    from starlette.requests import Request as StarletteRequest
    from starlette.responses import Response as StarletteResponse

    # Create a scope from the incoming request
    scope = {
        "type": "http",
        "method": request.method,
        "path": request.url.path,
        "query_string": request.url.query.encode() if request.url.query else b"",
        "headers": [
            (k.lower().encode(), v.encode()) for k, v in request.headers.items()
        ],
        "server": ("localhost", 443),
        "client": ("0.0.0.0", 0),
        "app": app,
        "env": env,
        "ctx": ctx,
    }

    # Handle CORS preflight
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin", "*")
        return Response(
            status_code=204,
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "86400",
            },
        )

    # Process request through ASGI app
    response = await app(scope, receive=lambda: request.body(), send=None)

    return Response(
        status_code=response.status_code,
        headers=dict(response.headers),
        body=response.body,
    )
