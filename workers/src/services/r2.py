"""R2 Storage service for uploading images to Cloudflare R2."""

import json
import js
from pyodide.ffi import to_js as _to_js
from js import Object


def to_js(obj):
    """Convert Python objects to JS with dict_converter for proper dict->Object mapping."""
    return _to_js(obj, dict_converter=Object.fromEntries)


R2_PUBLIC_BASE = "https://pub-ae92531aa2144de7aad7a3510e7b31ff.r2.dev"


async def upload_vton_result(env, user_id: str, vton_id: str, image_bytes: bytes) -> str:
    """Upload VTON result image to R2 and return the public URL.

    Stores at: vton/{user_id}/{vton_id}.jpg
    """
    key = f"vton/{user_id}/{vton_id}.jpg"

    await env.R2.put(
        key,
        image_bytes,
        to_js({"httpMetadata": {"contentType": "image/jpeg"}}),
    )

    return f"{R2_PUBLIC_BASE}/{key}"


async def download_image_as_bytes(url: str) -> bytes:
    """Download an image from a URL and return raw bytes."""
    resp = await js.fetch(url, to_js({"method": "GET"}))
    if int(resp.status) >= 400:
        raise Exception(f"Failed to download image: {resp.status}")
    array_buffer = await resp.arrayBuffer()
    return js.Uint8Array.new(array_buffer).to_py()


async def upload_profile_image(env, user_id: str, image_bytes: bytes, content_type: str = "image/jpeg") -> str:
    """Upload user profile image to R2 and return the public URL.

    Stores at: profiles/{user_id}/avatar.jpg
    """
    key = f"profiles/{user_id}/avatar.jpg"

    try:
        await env.R2.put(
            key,
            image_bytes,
            to_js({"httpMetadata": {"contentType": content_type}}),
        )
    except Exception as e:
        print(json.dumps({
            "event": "r2_put_error",
            "key": key,
            "image_bytes_len": len(image_bytes),
            "content_type": content_type,
            "error": str(e),
            "error_type": type(e).__name__,
        }))
        raise

    return f"{R2_PUBLIC_BASE}/{key}"


async def save_vton_output_to_r2(env, user_id: str, vton_id: str, output_url: str) -> str:
    """Download YouCam output and upload to R2. Returns R2 public URL.

    This ensures VTON result images persist even if freeimage.host URLs expire.
    Returns R2 URL on success, original URL on failure (with detailed error logging).
    """
    if not output_url:
        print(json.dumps({
            "event": "r2_save_skip",
            "vton_id": vton_id,
            "reason": "empty_output_url",
        }))
        return output_url

    try:
        image_bytes = await download_image_as_bytes(output_url)
        r2_url = await upload_vton_result(env, user_id, vton_id, image_bytes)
        print(json.dumps({
            "event": "r2_save_ok",
            "vton_id": vton_id,
            "original_len": len(image_bytes),
            "r2_url": r2_url,
        }))
        return r2_url
    except Exception as e:
        print(json.dumps({
            "event": "r2_save_failed",
            "vton_id": vton_id,
            "output_url": output_url[:100] if output_url else "none",
            "error": str(e),
            "error_type": type(e).__name__,
        }))
        return output_url


async def delete_vton_result(env, user_id: str, vton_id: str) -> bool:
    """Delete VTON result image from R2."""
    key = f"vton/{user_id}/{vton_id}.jpg"
    await env.R2.delete(key)
    return True
