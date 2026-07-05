"""FT-LineOne API - Cloudflare Workers Python Entry Point."""

import json
import time

from workers import WorkerEntrypoint, Response

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import asgi

from routes import auth, products, vton, recommendations, scrapers, users, favorites
from services.database import DatabaseService

app = FastAPI(
    title="FT-LineOne API",
    description="Fashion Try-On Platform API - Cloudflare Workers",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS middleware — hardcoded because os.getenv doesn't work in Workers Python
# (vars only arrive via self.env, which isn't available at import time)
CORS_ORIGINS = [
    "https://thelineone.com",
    "https://www.thelineone.com",
    "http://localhost:3000",
    "https://feat-cloudflare-migration.ft-lineone.pages.dev",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


def _cors_headers(origin):
    origins = CORS_ORIGINS
    if origin and origin in origins:
        allow_origin = origin
    else:
        allow_origin = origins[0] if origins else "*"
    return {
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Max-Age": "86400",
    }


# Exception handler — catches unhandled exceptions that escape FastAPI/Starlette
# and returns them WITH CORS headers so the browser shows the real error
# instead of a misleading "network error" / CORS block.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    import traceback
    origin = request.headers.get("origin", "")
    headers = _cors_headers(origin)
    headers["Content-Type"] = "application/json"
    print(json.dumps({
        "event": "unhandled_exception",
        "url": str(request.url),
        "method": request.method,
        "error": str(exc),
        "traceback": traceback.format_exc(),
    }))
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
        headers=headers,
    )


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(vton.router, prefix="/api/v1/vton", tags=["VTON"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])
app.include_router(scrapers.router, prefix="/api/v1/scrapers", tags=["Scrapers"])
app.include_router(favorites.router, prefix="/api/v1/favorites", tags=["Favorites"])


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
        origin = request.headers.get("origin", "")

        if request.method == "OPTIONS":
            h = _cors_headers(origin)
            h["Content-Type"] = "text/plain"
            return Response(b"", status=204, headers=h)

        start = time.time()
        app.state.db = DatabaseService(self.env)
        app.state.env = self.env

        try:
            response = await asgi.fetch(app, request, self.env)
            elapsed = round((time.time() - start) * 1000)
            print(json.dumps({
                "method": request.method,
                "url": request.url,
                "status": response.status_code if hasattr(response, "status_code") else 200,
                "ms": elapsed,
            }))
            return response
        except Exception as e:
            elapsed = round((time.time() - start) * 1000)
            import traceback
            print(json.dumps({
                "method": request.method,
                "url": request.url,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "ms": elapsed,
            }))
            h = _cors_headers(origin)
            h["Content-Type"] = "application/json"
            return Response(
                json.dumps({"detail": str(e)}).encode("utf-8"),
                status=500,
                headers=h,
            )
        except BaseException as e:
            elapsed = round((time.time() - start) * 1000)
            print(json.dumps({
                "method": request.method,
                "url": request.url,
                "error": f"BaseException: {e}",
                "ms": elapsed,
            }))
            h = _cors_headers(origin)
            h["Content-Type"] = "application/json"
            return Response(
                json.dumps({"detail": "Internal server error"}).encode("utf-8"),
                status=500,
                headers=h,
            )

    async def on_scheduled(self, controller):
        """Handle cron triggers for scraper scheduling and VTON polling."""
        from scrapers.scheduler import ScraperRunner
        from cron import process_pending_vton_tasks

        cron_expr = getattr(controller, "cron", "") or ""
        max_products = 20

        print(json.dumps({"event": "cron_start", "cron": cron_expr}))

        # Run scrapers (independent — failure doesn't block VTON)
        try:
            runner = ScraperRunner(self.env, max_products=max_products)
            try:
                results = await runner.run_all_scrapers()
                print(json.dumps({"event": "cron_scrapers_complete", "cron": cron_expr, "results": results}))
            finally:
                await runner.close()
        except Exception as e:
            print(json.dumps({"event": "cron_scrapers_error", "error": str(e)}))

        # Process pending VTON tasks (always runs, even if scrapers failed)
        try:
            vton_results = await process_pending_vton_tasks(self.env)
            print(json.dumps({"event": "cron_vton_complete", "cron": cron_expr, "results": vton_results}))
        except Exception as e:
            print(json.dumps({"event": "cron_vton_error", "error": str(e)}))
