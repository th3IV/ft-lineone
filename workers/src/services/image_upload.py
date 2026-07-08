"""Image upload service — uploads user/garment photos to get public URLs.

YouCam cannot download from Cloudflare Workers domains OR most e-commerce CDNs
(mauiandsons.cl, static.zara.net, etc.) — blocked by bot protection.
We work around this by uploading images to freeimage.host which provides
permanent public URLs that YouCam CAN access.
"""

import json
import base64
import js
from pyodide.ffi import to_js as _to_js
from js import Object


def to_js(obj):
    return _to_js(obj, dict_converter=Object.fromEntries)


FREEIMAGE_API = "https://freeimage.host/api/1/upload"
FREEIMAGE_KEY_FALLBACK = "6d207e02198a847aa98d0a2a901485a5"


def _url_encode_b64(b64: str) -> str:
    """URL-encode base64 string (+, /, = need encoding for form body)."""
    return b64.replace("+", "%2B").replace("/", "%2F").replace("=", "%3D")


async def _upload_to_freeimage(base64_data: str, filename: str = "photo.jpg", api_key: str = "") -> str:
    """Upload a base64 image to freeimage.host and return the public URL."""
    key = api_key or FREEIMAGE_KEY_FALLBACK
    encoded = _url_encode_b64(base64_data)
    body = f"key={key}&image={encoded}&format=json"

    resp = await js.fetch(
        FREEIMAGE_API,
        to_js({
            "method": "POST",
            "headers": {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            "body": body,
        }),
    )

    text = await resp.text()
    data = json.loads(text)

    if int(resp.status) != 200 or data.get("status_code") != 200:
        error = data.get("error", {}).get("message", "") or text[:200]
        raise Exception(f"Image upload failed ({resp.status}): {error}")

    url = data.get("image", {}).get("url")
    if not url:
        raise Exception(f"No URL in upload response: {text[:200]}")

    return url


async def upload_user_photo(base64_data: str, filename: str = "photo.jpg", api_key: str = "") -> str:
    """Upload a base64 user photo to freeimage.host and return the public URL.

    Args:
        base64_data: Raw base64 string (WITHOUT the data:...;base64, prefix).
        filename: Desired filename for the upload.
        api_key: freeimage.host API key (falls back to hardcoded if empty).

    Returns:
        Public HTTPS URL of the uploaded image.
    """
    return await _upload_to_freeimage(base64_data, filename, api_key)


async def upload_garment_image(image_url: str, api_key: str = "") -> str:
    """Download a garment image from any URL and re-upload to freeimage.host.

    YouCam blocks most e-commerce CDNs (mauiandsons.cl, static.zara.net, etc.).
    This function downloads the image via JS fetch with browser-like headers,
    converts to base64, and uploads to freeimage.host which YouCam CAN access.

    Args:
        image_url: Original garment image URL (may be blocked by YouCam).

    Returns:
        Public HTTPS URL on freeimage.host.
    """
    # Fetch garment image with browser-like headers to avoid bot protection
    resp = await js.fetch(image_url, to_js({
        "method": "GET",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
        },
    }))

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

    return await _upload_to_freeimage(b64, "garment.jpg", api_key)
