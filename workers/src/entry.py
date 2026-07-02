"""FT-LineOne API - Cloudflare Workers Python Entry Point."""

import os
import json
import time

from workers import WorkerEntrypoint, Response

from fastapi import FastAPI, Request
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


class Default(WorkerEntrypoint):
    """Cloudflare Workers Python entry point."""

    async def on_fetch(self, request):
        """Handle incoming HTTP requests via ASGI bridge."""
        start = time.time()
        app.state.db = DatabaseService(self.env)
        app.state.env = self.env

        try:
            response = await asgi.fetch(app, request, self.env)
            elapsed = round((time.time() - start) * 1000)
            print(json.dumps({
                "method": request.method,
                "url": request.url,
                "status": response.status if hasattr(response, "status") else 200,
                "ms": elapsed,
            }))
            return response
        except Exception as e:
            elapsed = round((time.time() - start) * 1000)
            print(json.dumps({
                "method": request.method,
                "url": request.url,
                "error": str(e),
                "ms": elapsed,
            }))
            raise

    async def on_scheduled(self, controller):
        """Handle cron triggers for scraper scheduling."""
        from scrapers.scheduler import ScraperRunner

        cron_expr = getattr(controller, "cron", "") or ""
        max_products = 20

        print(json.dumps({"event": "cron_start", "cron": cron_expr}))
        runner = ScraperRunner(self.env, max_products=max_products)
        try:
            results = await runner.run_all_scrapers()
            print(json.dumps({"event": "cron_complete", "cron": cron_expr, "results": results}))
        finally:
            await runner.close()
