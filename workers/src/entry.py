"""FT-LineOne API - Cloudflare Workers Python Entry Point."""

import asyncio
import hashlib
import json
import re
import time

from workers import WorkerEntrypoint, Response

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

import asgi

from routes import auth, products, vton, recommendations, scrapers, users, favorites, payments
from services.database import DatabaseService

app = FastAPI(
    title="FT-LineOne API",
    description="Fashion Try-On Platform API - Cloudflare Workers",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS origins — production domains only
_CORS_ORIGINS = [
    "https://thelineone.com",
    "https://www.thelineone.com",
]
_DEV_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]
_PAGES_PATTERN = re.compile(r"^https://([a-z0-9-]+\.)?ft-lineone\.pages\.dev$")


def _is_allowed_origin(origin: str) -> bool:
    """Check if origin is in the allowed list."""
    if not origin:
        return False
    if origin in _CORS_ORIGINS:
        return True
    if _PAGES_PATTERN.match(origin):
        return True
    # Allow dev origins only in non-production environments
    is_dev = _ENV.get("ENVIRONMENT", "production") not in ("production", "prod")
    if is_dev and origin in _DEV_ORIGINS:
        return True
    return False


_ENV = {}  # Set once on first request; used by CORS functions


def _cors_headers(origin):
    allow_origin = origin if _is_allowed_origin(origin) else _CORS_ORIGINS[0]
    return {
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Max-Age": "86400",
    }


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")
        if request.method == "OPTIONS":
            h = _cors_headers(origin)
            h["Content-Type"] = "text/plain"
            return Response(b"", status=204, headers=h)
        response = await call_next(request)
        if origin and _is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "86400"
        return response


app.add_middleware(DynamicCORSMiddleware)


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
        content={"detail": "Internal server error"},
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
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0", "runtime": "cloudflare-workers"}


@app.get("/test-packages")
async def test_packages(request: Request):
    """Test which Python packages are available in Workers. Requires admin."""
    from middleware.security import require_admin as _require_admin
    user = await _require_admin(request)
    results = {}

    # Test httpx
    try:
        import httpx
        results["httpx"] = {"available": True, "version": httpx.__version__}
    except ImportError as e:
        results["httpx"] = {"available": False, "error": str(e)}

    # Test cloudscraper
    try:
        import cloudscraper
        results["cloudscraper"] = {"available": True}
    except ImportError as e:
        results["cloudscraper"] = {"available": False, "error": str(e)}

    # Test curl_cffi
    try:
        import curl_cffi
        results["curl_cffi"] = {"available": True}
    except ImportError as e:
        results["curl_cffi"] = {"available": False, "error": str(e)}

    # Test js (Pyodide)
    try:
        import js
        results["js"] = {"available": True}
    except ImportError as e:
        results["js"] = {"available": False, "error": str(e)}

    return results


@app.get("/test-ai")
async def test_ai(request: Request):
    """Test endpoint to verify Workers AI binding is working. Requires admin."""
    from middleware.security import require_admin as _require_admin
    user = await _require_admin(request)
    env = getattr(request.app.state, "env", None)
    if not env or not hasattr(env, "AI"):
        return {"error": "AI binding not found", "has_env": env is not None}

    # Test 1: Check if AI object exists
    ai = env.AI
    ai_type = type(ai).__name__

    # Test 2: Try different models
    models_to_try = [
        "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        "@cf/meta/llama-3.1-70b-instruct",
        "@cf/meta/llama-3-8b-instruct",
        "@cf/meta/llama-3.2-3b-instruct",
        "@cf/meta/llama-3.1-8b-instruct-fast",
    ]

    results = {}
    working_model = None
    for model in models_to_try:
        try:
            result = await ai.run(
                model,
                {
                    "messages": [{"role": "user", "content": "Say hello in one word"}],
                    "max_tokens": 10,
                },
            )
            results[model] = {"success": True, "result": str(result)[:100]}
            if not working_model:
                working_model = model
        except Exception as e:
            error_msg = str(e)
            if "5028" in error_msg:
                results[model] = {"success": False, "error": "Model deprecated"}
            else:
                results[model] = {"success": False, "error": error_msg[:100]}

    return {
        "ai_type": ai_type,
        "working_model": working_model,
        "results": results,
    }


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
        global _ENV
        if not _ENV and hasattr(self, 'env'):
            _ENV = dict(self.env)
        origin = request.headers.get("origin", "")
        request_id = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]

        # CORS validation — reject non-whitelisted origins on non-OPTIONS
        if origin and request.method != "OPTIONS" and not _is_allowed_origin(origin):
            h = _cors_headers(origin)
            h["Content-Type"] = "application/json"
            h["X-Request-ID"] = request_id
            return Response(
                json.dumps({"detail": "Origin not allowed"}).encode("utf-8"),
                status=403,
                headers=h,
            )

        if request.method == "OPTIONS":
            h = _cors_headers(origin)
            h["Content-Type"] = "text/plain"
            h["X-Request-ID"] = request_id
            return Response(b"", status=204, headers=h)

        start = time.time()

        try:
            app.state.db = DatabaseService(self.env)
            app.state.env = self.env
        except Exception as e:
            import traceback
            print(json.dumps({
                "ts": int(start * 1000),
                "level": "error",
                "event": "init_error",
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "error": str(e),
                "traceback": traceback.format_exc(),
            }))
            h = _cors_headers(origin)
            h["Content-Type"] = "application/json"
            h["X-Request-ID"] = request_id
            return Response(
                json.dumps({"detail": "Service initialization error"}).encode("utf-8"),
                status=500,
                headers=h,
            )

        try:
            response = await asgi.fetch(app, request, self.env)
            elapsed = round((time.time() - start) * 1000)
            status = response.status_code if hasattr(response, "status_code") else 200
            print(json.dumps({
                "ts": int(start * 1000),
                "level": "info",
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "status": status,
                "ms": elapsed,
            }))
            return response
        except Exception as e:
            elapsed = round((time.time() - start) * 1000)
            import traceback
            print(json.dumps({
                "ts": int(start * 1000),
                "level": "error",
                "event": "unhandled_exception",
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "error": str(e),
                "traceback": traceback.format_exc(),
                "ms": elapsed,
            }))
            h = _cors_headers(origin)
            h["Content-Type"] = "application/json"
            h["X-Request-ID"] = request_id
            return Response(
                json.dumps({"detail": "Internal server error"}).encode("utf-8"),
                status=500,
                headers=h,
            )
        except BaseException as e:
            elapsed = round((time.time() - start) * 1000)
            print(json.dumps({
                "ts": int(start * 1000),
                "level": "error",
                "event": "base_exception",
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "error": f"BaseException: {e}",
                "ms": elapsed,
            }))
            h = _cors_headers(origin)
            h["Content-Type"] = "application/json"
            h["X-Request-ID"] = request_id
            return Response(
                json.dumps({"detail": "Internal server error"}).encode("utf-8"),
                status=500,
                headers=h,
            )

    async def scheduled(self, controller, env, ctx):
        """Handle cron triggers for scraper scheduling and VTON polling."""
        from scrapers.scheduler import ScraperRunner
        from cron import process_pending_vton_tasks, cleanup_corrupted_data

        cron_expr = getattr(controller, "cron", "") or ""
        max_products = 20

        print(json.dumps({"event": "cron_start", "cron": cron_expr}))

        # Run scrapers (independent — failure doesn't block VTON)
        # Timeout: 25s to ensure VTON polling and cleanup always run
        try:
            runner = ScraperRunner(env, max_products=max_products)
            try:
                results = await asyncio.wait_for(runner.run_all_scrapers(), timeout=25)
                print(json.dumps({"event": "cron_scrapers_complete", "cron": cron_expr, "results": results}))
            except asyncio.TimeoutError:
                print(json.dumps({"event": "cron_scrapers_timeout", "cron": cron_expr}))
            finally:
                await runner.close()
        except Exception as e:
            print(json.dumps({"event": "cron_scrapers_error", "error": str(e)}))

        # Process pending VTON tasks (always runs, even if scrapers failed)
        try:
            vton_results = await process_pending_vton_tasks(env)
            print(json.dumps({"event": "cron_vton_complete", "cron": cron_expr, "results": vton_results}))
        except Exception as e:
            print(json.dumps({"event": "cron_vton_error", "error": str(e)}))

        # Clean up corrupted product data (capped at 10s)
        try:
            cleanup_results = await asyncio.wait_for(cleanup_corrupted_data(env), timeout=10)
            print(json.dumps({"event": "cron_cleanup_complete", "cron": cron_expr, "results": cleanup_results}))
        except asyncio.TimeoutError:
            print(json.dumps({"event": "cron_cleanup_timeout", "cron": cron_expr}))
        except Exception as e:
            print(json.dumps({"event": "cron_cleanup_error", "error": str(e)}))
