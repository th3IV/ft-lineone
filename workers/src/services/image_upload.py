"""Image upload service — uploads user photos to get public URLs.

YouCam cannot download from Cloudflare Workers domains (blocked by their
CDN/bot protection).  We work around this by uploading the user's photo to
freeimage.host which provides permanent public URLs that YouCam CAN access.
"""

import json
import js
from pyodide.ffi import to_js as _to_js
from js import Object


def to_js(obj):
    return _to_js(obj, dict_converter=Object.fromEntries)


FREEIMAGE_API = "https://freeimage.host/api/1/upload"
FREEIMAGE_KEY = "6d207e02198a847aa98d0a2a901485a5"


def _url_encode_b64(b64: str) -> str:
    """URL-encode base64 string (+, /, = need encoding for form body)."""
    return b64.replace("+", "%2B").replace("/", "%2F").replace("=", "%3D")


async def upload_user_photo(base64_data: str, filename: str = "photo.jpg") -> str:
    """Upload a base64 image to freeimage.host and return the public URL.

    Args:
        base64_data: Raw base64 string (WITHOUT the data:...;base64, prefix).
        filename: Desired filename for the upload.

    Returns:
        Public HTTPS URL of the uploaded image.
    """
    # URL-encode the base64 for form body (+, /, = are special in URL encoding)
    encoded = _url_encode_b64(base64_data)
    body = f"key={FREEIMAGE_KEY}&image={encoded}&format=json"

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
