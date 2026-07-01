"""FT-LineOne API - Cloudflare Workers Python Entry Point."""

import os
from typing import Any

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

import asgi

from routes import auth, products, vton, recommendations, scrapers
from services.database import DatabaseService

app = FastAPI(
    title="FT-LineOne API",
    description="Fashion Try-On Platform API - Cloudflare Workers",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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


class Default:
    """Cloudflare Workers Python entry point."""

    def __init__(self, env: Any):
        self.env = env

    async def fetch(self, request: Any) -> Response:
        """Handle incoming HTTP requests via ASGI bridge."""
        # Attach env and db to app.state for route access
        app.state.env = self.env
        app.state.db = DatabaseService(self.env)
        return await asgi.fetch(app, request, self.env)

    async def scheduled(self, controller: Any, env: Any, ctx: Any) -> None:
        """Handle cron triggers for scraper scheduling."""
        from scrapers.scheduler import ScraperRunner

        runner = ScraperRunner(env)
        try:
            results = await runner.run_all_scrapers()
            print(f"Cron completed: {results}")
        finally:
            await runner.close()
