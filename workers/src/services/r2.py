"""R2 Storage service for uploading images to Cloudflare R2."""

import json
import time
import hmac
import hashlib
import urllib.parse
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


async def generate_presigned_upload_url(env, key: str, content_type: str = "image/jpeg", expiration_seconds: int = 3600) -> dict:
    """Generate a presigned PUT URL for direct browser upload to R2.
    
    Returns: {"upload_url": "...", "get_url": "...", "key": "...", "expires_in": expiration_seconds}
    """
    # R2 presigned URLs via S3-compatible API
    # We use the R2 S3 API endpoint to generate presigned URLs
    import time
    import hmac
    import hashlib
    import urllib.parse
    
    account_id = getattr(env, "R2_ACCOUNT_ID", None)
    access_key = getattr(env, "R2_ACCESS_KEY_ID", None)
    secret_key = getattr(env, "R2_SECRET_ACCESS_KEY", None)
    bucket = getattr(env, "R2_BUCKET", "r2-thelineone01")
    
    if not all([account_id, access_key, secret_key]):
        # Fallback: return a public URL pattern (requires public bucket)
        public_url = f"{R2_PUBLIC_BASE}/{key}"
        return {
            "upload_url": public_url,  # Not truly presigned, but works for public buckets
            "get_url": public_url,
            "key": key,
            "expires_in": expiration_seconds,
        }
    
    # S3 Signature Version 4 for presigned URL
    region = "auto"
    service = "s3"
    algorithm = "AWS4-HMAC-SHA256"
    
    now = int(time.time())
    date = time.strftime("%Y%m%d", time.gmtime(now))
    amz_date = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(now))
    
    credential_scope = f"{date}/{region}/{service}/aws4_request"
    
    # Canonical request for PUT
    canonical_uri = f"/{bucket}/{urllib.parse.quote(key, safe='')}"
    canonical_querystring = (
        f"X-Amz-Algorithm={algorithm}&"
        f"X-Amz-Credential={urllib.parse.quote(access_key + '/' + credential_scope)}&"
        f"X-Amz-Date={amz_date}&"
        f"X-Amz-Expires={expiration_seconds}&"
        f"X-Amz-SignedHeaders=content-type;host"
    )
    
    canonical_headers = f"content-type:{content_type}\nhost:{bucket}.{account_id}.r2.cloudflarestorage.com\n"
    signed_headers = "content-type;host"
    
    # Empty payload hash for PUT
    payload_hash = hashlib.sha256(b"").hexdigest()
    
    canonical_request = f"PUT\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    
    string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
    
    # Signing key
    k_date = hmac.new(("AWS4" + secret_key).encode(), date.encode(), hashlib.sha256).digest()
    k_region = hmac.new(k_date, region.encode(), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode(), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, credential_scope.encode(), hashlib.sha256).digest()
    
    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
    
    presigned_url = (
        f"https://{bucket}.{account_id}.r2.cloudflarestorage.com{canonical_uri}"
        f"?{canonical_querystring}&X-Amz-Signature={signature}"
    )
    
    return {
        "upload_url": presigned_url,
        "get_url": f"{R2_PUBLIC_BASE}/{key}",
        "key": key,
        "expires_in": expiration_seconds,
    }
