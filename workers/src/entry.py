"""FT-LineOne API - Cloudflare Workers Python Entry Point."""

import hashlib
import json
import re
import time

import js
from js import Headers

from workers import WorkerEntrypoint, Response

# Register Durable Object class (required for wrangler durable_objects binding)
from durable_objects.scraper_worker import ScraperWorkerEntrypoint  # noqa: F401

from fastapi import FastAPI, Request

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


def _is_allowed_origin(origin, env_obj=None):
    """Check if origin is in the allowed list."""
    if not origin:
        return False
    if origin in _CORS_ORIGINS:
        return True
    if _PAGES_PATTERN.match(origin):
        return True
    # Only allow dev origins in non-production environments
    environment = "production"
    if env_obj is not None:
        try:
            environment = getattr(env_obj, "ENVIRONMENT", "production")
        except Exception:
            pass
    if environment not in ("production", "prod") and origin in _DEV_ORIGINS:
        return True
    return False


def _cors_headers(origin, env_obj=None):
    allow_origin = origin if _is_allowed_origin(origin, env_obj) else _CORS_ORIGINS[0]
    return {
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Max-Age": "86400",
    }


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
        request_id = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]

        # CORS validation — reject non-whitelisted origins on non-OPTIONS
        if origin and request.method != "OPTIONS" and not _is_allowed_origin(origin, self.env):
            h = _cors_headers(origin, self.env)
            h["Content-Type"] = "application/json"
            h["X-Request-ID"] = request_id
            return Response(
                json.dumps({"detail": "Origin not allowed"}).encode("utf-8"),
                status=403,
                headers=h,
            )

        if request.method == "OPTIONS":
            h = _cors_headers(origin, self.env)
            h["Content-Type"] = "text/plain"
            h["X-Request-ID"] = request_id
            return Response(b"", status=204, headers=h)

        start = time.time()

        try:
            app.state.db = DatabaseService(self.env)
            app.state.env = self.env
            if hasattr(self.env, "PREMIUM_KV"):
                from services.kv_premium import PremiumKVService
                app.state.kv_premium = PremiumKVService(self.env.PREMIUM_KV)
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
            h = _cors_headers(origin, self.env)
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

            # js.Response headers are immutable after body is constructed.
            # Read body, then create a NEW Response with CORS headers merged.
            resp_status = response.status if hasattr(response, "status") else 200
            resp_headers = {}
            try:
                js_headers = response.headers
                if hasattr(js_headers, "entries"):
                    for entry in js_headers.entries():
                        # entry is a JS array [key, value]
                        resp_headers[str(entry[0])] = str(entry[1])
            except Exception:
                pass

            # Streaming responses (SSE): pass body through untouched.
            # Buffering a ReadableStream with arrayBuffer() kills the stream.
            resp_content_type = resp_headers.get("content-type", "").lower()
            if "text/event-stream" in resp_content_type:
                stream_headers = Headers.new(response.headers)
                for k, v in _cors_headers(origin, self.env).items():
                    stream_headers.set(k, v)
                stream_headers.set("X-Request-ID", request_id)
                print(json.dumps({
                    "ts": int(start * 1000),
                    "level": "info",
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "status": resp_status,
                    "stream": True,
                    "ms": elapsed,
                }))
                return Response(response.body, status=resp_status, headers=stream_headers)

            body = b""
            try:
                body_bytes = await response.arrayBuffer()
                if body_bytes is not None:
                    # JsProxy(ArrayBuffer) -> memoryview -> bytes
                    body = bytes(body_bytes.to_py())
            except Exception:
                pass

            # Merge CORS headers onto the response
            cors_h = _cors_headers(origin, self.env)
            for k, v in cors_h.items():
                resp_headers[k] = v
            resp_headers["X-Request-ID"] = request_id

            print(json.dumps({
                "ts": int(start * 1000),
                "level": "info",
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "status": resp_status,
                "ms": elapsed,
            }))

            return Response(body, status=resp_status, headers=resp_headers)
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
            h = _cors_headers(origin, self.env)
            h["Content-Type"] = "application/json"
            h["X-Request-ID"] = request_id
            return Response(
                json.dumps({"detail": "Internal server error"}).encode("utf-8"),
                status=500,
                headers=h,
            )

    async def queue(self, batch, env, ctx):
        """Handle queue messages for scraper jobs."""
        from scrapers.scheduler import ScraperRunner

        message_count = len(batch.messages)
        print(json.dumps({"event": "queue_batch_received", "count": message_count}))

        runner = ScraperRunner(self.env)
        try:
            for message in batch.messages:
                body = message.body
                store = body.get("store", "unknown")
                max_products = body.get("max_products", 20)
                attempts = getattr(message, "attempts", 1) or 1
                try:
                    result = await runner.run_single_store(store, max_products)
                    if result.get("status") == "completed":
                        message.ack()
                        print(json.dumps({"event": "queue_store_done", "store": store, "result": result}))
                    else:
                        # Logical failure inside scraper — retry instead of acking.
                        delay = min(30 * (2 ** max(0, attempts - 1)), 43200)
                        message.retry(delaySeconds=delay)
                        print(json.dumps({
                            "event": "queue_store_failed",
                            "store": store,
                            "error": result.get("error", "unknown"),
                            "retry_in": delay,
                        }))
                except Exception as e:
                    delay = min(30 * (2 ** max(0, attempts - 1)), 43200)
                    message.retry(delaySeconds=delay)
                    print(json.dumps({"event": "queue_store_error", "store": store, "error": str(e), "retry_in": delay}))
        finally:
            try:
                await runner.close()
            except Exception:
                pass
