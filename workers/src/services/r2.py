"""R2 Storage service for uploading VTON result images."""

import base64


R2_PUBLIC_BASE = "https://pub-ae92531aa2144de7aad7a3510e7b31ff.r2.dev"


async def upload_vton_result(env, user_id: str, vton_id: str, image_bytes: bytes) -> str:
    """Upload VTON result image to R2 and return the public URL.

    Stores at: vton/{user_id}/{vton_id}.jpg
    """
    key = f"vton/{user_id}/{vton_id}.jpg"

    await env.BUCKET.put(
        key,
        image_bytes,
        http_metadata={"contentType": "image/jpeg"},
    )

    return f"{R2_PUBLIC_BASE}/{key}"


async def download_image_as_bytes(url: str) -> bytes:
    """Download an image from a URL and return raw bytes."""
    import httpx

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.bytes


async def save_vton_output_to_r2(env, user_id: str, vton_id: str, output_url: str) -> str:
    """Download YouCam output and upload to R2. Returns R2 public URL.

    This ensures VTON result images persist even if freeimage.host URLs expire.
    """
    try:
        image_bytes = await download_image_as_bytes(output_url)
        r2_url = await upload_vton_result(env, user_id, vton_id, image_bytes)
        return r2_url
    except Exception as e:
        # If R2 upload fails, fall back to the original URL
        import json
        print(json.dumps({
            "event": "r2_upload_failed",
            "vton_id": vton_id,
            "error": str(e),
        }))
        return output_url
