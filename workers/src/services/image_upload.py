"""Image upload service — uploads user/garment photos to get public URLs.

YouCam cannot download from Cloudflare Workers domains OR most e-commerce CDNs
(mauiandsons.cl, static.zara.net, etc.) — blocked by bot protection.
We work around this by uploading images to freeimage.host which provides
permanent public URLs that YouCam CAN access.

Resilience features:
  - Circuit breaker: stops calling freeimage.host after N consecutive failures
  - Retry with exponential backoff: 3 attempts with 0s, 1s, 2s delays
  - Timeout: 15s for uploads, 10s for downloads
"""

import json
import base64
import time
import js
from pyodide.ffi import to_js as _to_js
from js import Object


def to_js(obj):
    return _to_js(obj, dict_converter=Object.fromEntries)


FREEIMAGE_API = "https://freeimage.host/api/1/upload"

# Circuit breaker state (persists across requests within same Worker instance)
_circuit = {
    "failures": 0,
    "open_until": 0,      # timestamp when circuit opens until
    "success_threshold": 2, # successes needed to close circuit from half-open
    "successes": 0,
}
CIRCUIT_FAILURE_THRESHOLD = 5
CIRCUIT_OPEN_DURATION = 60  # seconds


def _circuit_is_open():
    """Check if circuit breaker is open (blocking requests)."""
    now = time.time()
    if _circuit["open_until"] > now:
        return True
    # Half-open state: allow one request through
    if _circuit["open_until"] > 0 and _circuit["open_until"] <= now:
        return False  # half-open: allow probe
    return False


def _circuit_record_success():
    """Record a successful call."""
    _circuit["failures"] = 0
    _circuit["open_until"] = 0
    _circuit["successes"] += 1


def _circuit_record_failure():
    """Record a failed call. Opens circuit if threshold reached."""
    _circuit["failures"] += 1
    _circuit["successes"] = 0
    if _circuit["failures"] >= CIRCUIT_FAILURE_THRESHOLD:
        _circuit["open_until"] = time.time() + CIRCUIT_OPEN_DURATION
        print(json.dumps({
            "event": "circuit_breaker_open",
            "failures": _circuit["failures"],
            "open_until_seconds": CIRCUIT_OPEN_DURATION,
        }))


def _url_encode_b64(b64: str) -> str:
    """URL-encode base64 string (+, /, = need encoding for form body)."""
    return b64.replace("+", "%2B").replace("/", "%2F").replace("=", "%3D")


async def _fetch_with_timeout(url, options, timeout_ms=15000):
    """Wrapper around js.fetch with AbortController timeout."""
    controller = js.AbortController.new()
    signal = controller.signal
    # Add signal to options
    opts = to_js({**options, "signal": signal})
    # Start timeout timer
    timer = js.setTimeout(lambda: controller.abort(), timeout_ms)
    try:
        resp = await js.fetch(url, opts)
        js.clearTimeout(timer)
        return resp
    except Exception as e:
        js.clearTimeout(timer)
        if "abort" in str(e).lower() or "timeout" in str(e).lower():
            raise Exception(f"Request timeout after {timeout_ms}ms: {url}")
        raise


async def _upload_to_freeimage(base64_data: str, filename: str = "photo.jpg", api_key: str = "") -> str:
    """Upload a base64 image to freeimage.host and return the public URL.

    Includes circuit breaker, retry with backoff, and timeout.
    """
    if _circuit_is_open():
        raise Exception(f"Circuit breaker OPEN — freeimage.host temporarily unavailable (retry in {CIRCUIT_OPEN_DURATION}s)")

    key = api_key
    if not key:
        raise Exception("No FreeImage API key provided. Set FREEIMAGE_KEY as a wrangler secret.")
    encoded = _url_encode_b64(base64_data)
    body = f"key={key}&image={encoded}&format=json"

    last_error = None
    for attempt in range(3):
        try:
            resp = await _fetch_with_timeout(
                FREEIMAGE_API,
                {
                    "method": "POST",
                    "headers": {"Content-Type": "application/x-www-form-urlencoded"},
                    "body": body,
                },
                timeout_ms=15000,
            )

            text = await resp.text()
            data = json.loads(text)

            if int(resp.status) != 200 or data.get("status_code") != 200:
                error = data.get("error", {}).get("message", "") or text[:200]
                raise Exception(f"Image upload failed ({resp.status}): {error}")

            url = data.get("image", {}).get("url")
            if not url:
                raise Exception(f"No URL in upload response: {text[:200]}")

            _circuit_record_success()
            return url

        except Exception as e:
            last_error = e
            error_str = str(e)

            # Don't retry on auth errors (401, 403) or bad request (400)
            if any(k in error_str for k in ["401", "403", "400", "auth", "permission"]):
                _circuit_record_failure()
                raise

            # Don't retry on circuit open
            if "Circuit breaker OPEN" in error_str:
                raise

            # Retry with backoff for transient errors
            if attempt < 2:
                delay = (2 ** attempt)  # 0s, 1s
                print(json.dumps({
                    "event": "freeimage_retry",
                    "attempt": attempt + 1,
                    "delay_ms": delay * 1000,
                    "error": error_str[:200],
                }))
                import asyncio
                await asyncio.sleep(delay)

    _circuit_record_failure()
    raise last_error


async def upload_user_photo(base64_data: str, filename: str = "photo.jpg", api_key: str = "", env=None) -> str:
    """Upload a base64 user photo and return the public URL.

    Tries R2 first (if env with R2 binding provided), then falls back to freeimage.host.

    Args:
        base64_data: Raw base64 string (WITHOUT the data:...;base64, prefix).
        filename: Desired filename for the upload.
        api_key: freeimage.host API key. If empty, tries FREEIMAGE_KEY from env.
        env: Cloudflare Worker env (for R2 binding and FREEIMAGE_KEY). If None, skips R2.

    Returns:
        Public HTTPS URL of the uploaded image.
    """
    # Try R2 first if available
    if env and hasattr(env, "R2"):
        try:
            import base64 as _b64
            key = f"vton/uploads/{filename}"
            image_bytes = _b64.b64decode(base64_data)
            content_type = "image/jpeg"
            if filename.endswith(".png"):
                content_type = "image/png"
            await env.R2.put(key, image_bytes, to_js({"httpMetadata": {"contentType": content_type}}))
            r2_url = f"https://pub-ae92531aa2144de7aad7a3510e7b31ff.r2.dev/{key}"
            print(json.dumps({"event": "upload_r2_ok", "key": key}))
            return r2_url
        except Exception as e:
            print(json.dumps({"event": "upload_r2_fallback", "error": str(e)[:200]}))

    # Fallback to freeimage.host
    if not api_key and env:
        api_key = getattr(env, "FREEIMAGE_KEY", "")
    return await _upload_to_freeimage(base64_data, filename, api_key)


async def upload_garment_image(image_url: str, api_key: str = "", env=None) -> str:
    """Download a garment image from any URL and re-upload to a public host.

    YouCam blocks most e-commerce CDNs (mauiandsons.cl, static.zara.net, etc.).
    This function downloads the image via JS fetch with browser-like headers,
    converts to base64, and uploads to R2 (if available) or freeimage.host.

    Args:
        image_url: Original garment image URL (may be blocked by YouCam).
        env: Cloudflare Worker env (for R2 binding). If None, skips R2.

    Returns:
        Public HTTPS URL on R2 or freeimage.host.
    """
    last_error = None
    for attempt in range(3):
        try:
            # Fetch garment image with browser-like headers to avoid bot protection
            resp = await _fetch_with_timeout(
                image_url,
                {
                    "method": "GET",
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Referer": "https://www.google.com/",
                    },
                },
                timeout_ms=10000,
            )

            status = int(resp.status)
            if status != 200:
                raise Exception(f"Failed to download garment image (HTTP {status})")

            # Read body as ArrayBuffer, convert to base64 via Python
            array_buf = await resp.arrayBuffer()
            uint8 = js.Uint8Array.new(array_buf)
            # Convert Uint8Array to Python bytes efficiently
            py_bytes = bytes(uint8.to_py())
            b64 = base64.b64encode(py_bytes).decode("ascii")

            if not b64 or len(b64) < 100:
                raise Exception("Downloaded image too small or empty")

            # Try R2 first if available
            if env and hasattr(env, "R2"):
                try:
                    key = f"vton/garments/garment_{int(time.time())}.jpg"
                    await env.R2.put(key, py_bytes, to_js({"httpMetadata": {"contentType": "image/jpeg"}}))
                    r2_url = f"https://pub-ae92531aa2144de7aad7a3510e7b31ff.r2.dev/{key}"
                    print(json.dumps({"event": "garment_upload_r2_ok", "key": key}))
                    return r2_url
                except Exception as e:
                    print(json.dumps({"event": "garment_upload_r2_fallback", "error": str(e)[:200]}))

            # Fallback to freeimage.host
            if not api_key and env:
                api_key = getattr(env, "FREEIMAGE_KEY", "")
            return await _upload_to_freeimage(b64, "garment.jpg", api_key)

        except Exception as e:
            last_error = e
            error_str = str(e)

            # Don't retry on auth/bad-request errors
            if any(k in error_str for k in ["401", "403", "400", "auth", "permission", "Circuit breaker OPEN"]):
                raise

            # Retry with backoff for transient errors
            if attempt < 2:
                delay = (2 ** attempt)  # 0s, 1s
                print(json.dumps({
                    "event": "garment_download_retry",
                    "attempt": attempt + 1,
                    "delay_ms": delay * 1000,
                    "error": error_str[:200],
                }))
                import asyncio
                await asyncio.sleep(delay)

    raise last_error
