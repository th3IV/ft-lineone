"""Virtual Try-On service using Cloudflare Workers AI."""

import base64
import os
import time


class VtonService:
    """VTON service using Cloudflare Workers AI (pruna/p-image-try-on)."""

    def __init__(self, env):
        self.env = env
        self.ai = env.AI  # Workers AI binding

    async def process_try_on(
        self,
        user_image_bytes: bytes,
        garment_image_url: str,
        product_id: str,
        user_id: str,
    ) -> dict:
        """Process a virtual try-on request using Workers AI."""
        try:
            if not self._validate_image(user_image_bytes):
                return {
                    "status": "failed",
                    "error": "Invalid image format. Please upload a JPEG or PNG file.",
                }

            result = await self.ai.run(
                "@cf/pruna/p-image-try-on",
                {
                    "person_image": base64.b64encode(user_image_bytes).decode("utf-8"),
                    "garment_image": garment_image_url,
                },
            )

            if result and "image" in result:
                result_image_bytes = base64.b64decode(result["image"])
                result_url = await self._store_result(
                    result_image_bytes, user_id, product_id
                )
                return {
                    "status": "completed",
                    "output_image_url": result_url,
                }
            else:
                return {
                    "status": "failed",
                    "error": "VTON model did not return a result",
                }

        except Exception as e:
            return {
                "status": "failed",
                "error": f"VTON processing failed: {str(e)}",
            }

    async def _store_result(
        self, image_bytes: bytes, user_id: str, product_id: str
    ) -> str:
        """Store the result image in R2 and return the URL."""
        content_type = self._detect_content_type(image_bytes)
        ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(content_type, "jpg")
        key = f"vton/results/{user_id}/{product_id}_{int(time.time())}.{ext}"

        await self.env.R2.put(
            key=key,
            body=image_bytes,
            http_metadata={"contentType": content_type},
        )

        bucket_name = getattr(self.env, "R2_BUCKET", None) or os.getenv("R2_BUCKET", "r2-thelineone01")
        account_id = getattr(self.env, "R2_ACCOUNT_ID", None) or os.getenv("R2_ACCOUNT_ID", "")
        return f"https://{bucket_name}.{account_id}.r2.dev/{key}"

    async def store_user_image(self, image_bytes: bytes, user_id: str) -> str:
        """Store user uploaded image in R2."""
        content_type = self._detect_content_type(image_bytes)
        ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(content_type, "jpg")
        key = f"vton/uploads/{user_id}/{int(time.time())}.{ext}"

        await self.env.R2.put(
            key=key,
            body=image_bytes,
            http_metadata={"contentType": content_type},
        )

        bucket_name = getattr(self.env, "R2_BUCKET", None) or os.getenv("R2_BUCKET", "r2-thelineone01")
        account_id = getattr(self.env, "R2_ACCOUNT_ID", None) or os.getenv("R2_ACCOUNT_ID", "")
        return f"https://{bucket_name}.{account_id}.r2.dev/{key}"

    @staticmethod
    def _detect_content_type(image_bytes: bytes) -> str:
        """Detect image content type from magic bytes."""
        if len(image_bytes) < 4:
            return "image/jpeg"
        header = image_bytes[:4]
        if header[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if header == b"\x89PNG":
            return "image/png"
        if header == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return "image/webp"
        return "image/jpeg"

    @staticmethod
    def _validate_image(image_bytes: bytes) -> bool:
        """Validate image by checking magic bytes."""
        if len(image_bytes) < 4:
            return False
        header = image_bytes[:4]
        if header[:3] == b"\xff\xd8\xff":
            return True
        if header == b"\x89PNG":
            return True
        if header == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return True
        return False
