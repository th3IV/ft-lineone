"""Cloudflare R2 Storage Service."""

import os
from typing import Optional


class R2Service:
    """R2 storage service for images and static assets."""

    def __init__(self, env):
        self.env = env
        self.r2 = env.R2  # R2 binding
        self.bucket_name = os.getenv("R2_BUCKET", "r2-thelineone01")
        self.account_id = os.getenv("R2_ACCOUNT_ID", "")

    async def upload_image(
        self,
        key: str,
        data: bytes,
        content_type: str = "image/jpeg",
    ) -> str:
        """Upload an image to R2.

        Args:
            key: The object key (path) in R2
            data: The image data as bytes
            content_type: The MIME type of the image

        Returns:
            The public URL of the uploaded image
        """
        try:
            await self.r2.put(
                key=key,
                body=data,
                http_metadata={"contentType": content_type},
            )

            return self._get_public_url(key)

        except Exception as e:
            raise Exception(f"Failed to upload image to R2: {str(e)}")

    async def get_image(self, key: str) -> Optional[bytes]:
        """Download an image from R2.

        Args:
            key: The object key (path) in R2

        Returns:
            The image data as bytes, or None if not found
        """
        try:
            result = await self.r2.get(key)
            if result:
                return await result.arrayBuffer()
            return None

        except Exception:
            return None

    async def delete_image(self, key: str) -> bool:
        """Delete an image from R2.

        Args:
            key: The object key (path) in R2

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            await self.r2.delete(key)
            return True
        except Exception:
            return False

    async def list_images(self, prefix: str = "") -> list[str]:
        """List all images with a given prefix.

        Args:
            prefix: The prefix to filter by

        Returns:
            List of object keys
        """
        try:
            result = await self.r2.list({"prefix": prefix})
            return [obj.key for obj in result.get("objects", [])]
        except Exception:
            return []

    def _get_public_url(self, key: str) -> str:
        """Generate the public URL for an R2 object."""
        # R2 public access URL format
        return f"https://{self.bucket_name}.{self.account_id}.r2.dev/{key}"

    def generate_product_key(self, store: str, product_id: str, filename: str) -> str:
        """Generate a safe key for product images."""
        import re
        # Sanitize filename
        safe_name = re.sub(r'[^\w\-_]', '_', filename)
        return f"products/{store}/{product_id}/{safe_name}"

    def generate_vton_key(self, user_id: str, product_id: str, is_result: bool = False) -> str:
        """Generate a safe key for VTON images."""
        import time
        suffix = "result" if is_result else "input"
        return f"vton/{user_id}/{product_id}_{suffix}_{int(time.time())}.jpg"
