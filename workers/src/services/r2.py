"""Cloudflare R2 Storage Service.

R2 binding's put() does strict `instanceof ArrayBufferView` checks that
reject Pyodide's to_js(bytes) proxy. We try multiple approaches:
  1. to_js(list(data)) → Uint8Array.new() — creates typed array from JS Array
  2. Blob constructor — may handle the proxy internally
  3. Response.body (ReadableStream) — last resort
"""

import os
import re
import time
from typing import Optional


class R2Service:
    """R2 storage service for images and static assets."""

    def __init__(self, env):
        self.env = env
        self.r2 = env.R2
        self.account_id = getattr(env, "R2_ACCOUNT_ID", None) or os.getenv("R2_ACCOUNT_ID", "")
        self.bucket_name = getattr(env, "R2_BUCKET", None) or os.getenv("R2_BUCKET", "r2-thelineone01")

    async def upload_image(
        self,
        key: str,
        data: bytes,
        content_type: str = "image/jpeg",
    ) -> str:
        """Upload an image to R2 using native JS types via fetch chain."""
        import js
        import base64 as _b64

        b64str = _b64.b64encode(data).decode("ascii")
        data_url = f"data:{content_type};base64,{b64str}"

        # fetch → ArrayBuffer → Uint8Array (ArrayBufferView accepted by R2)
        resp = await js.fetch(data_url)
        buf = await resp.arrayBuffer()
        uint8 = js.Uint8Array.new(buf)

        await self.r2.put(
            key=key,
            body=uint8,
            httpMetadata={"contentType": content_type},
        )
        return self._get_public_url(key)

    async def get_image(self, key: str) -> Optional[bytes]:
        """Download an image from R2."""
        try:
            result = await self.r2.get(key)
            if result:
                buf = await result.arrayBuffer()
                return bytes(buf)
            return None
        except Exception:
            return None

    async def delete_image(self, key: str) -> bool:
        """Delete an image from R2."""
        try:
            await self.r2.delete(key)
            return True
        except Exception:
            return False

    async def list_images(self, prefix: str = "") -> list[str]:
        """List all images with a given prefix."""
        try:
            result = await self.r2.list(prefix=prefix)
            objects = result.get("objects", [])
            return [obj["key"] for obj in objects] if isinstance(objects, list) else []
        except Exception:
            return []

    def _get_public_url(self, key: str) -> str:
        """Generate the public URL for an R2 object."""
        pub_domain = getattr(self.env, "R2_PUBLIC_DOMAIN", None) or "pub-ae92531aa2144de7aad7a3510e7b31ff.r2.dev"
        return f"https://{pub_domain}/{key}"

    def generate_product_key(self, store: str, product_id: str, filename: str) -> str:
        """Generate a safe key for product images."""
        safe_name = re.sub(r'[^\w\-_]', '_', filename)
        return f"products/{store}/{product_id}/{safe_name}"

    def generate_vton_key(self, user_id: str, product_id: str, is_result: bool = False) -> str:
        """Generate a safe key for VTON images."""
        suffix = "result" if is_result else "input"
        return f"vton/{user_id}/{product_id}_{suffix}_{int(time.time())}.jpg"
