"""Virtual Try-On service using Cloudflare Workers AI."""

import base64
import io
import os
from typing import Optional

from PIL import Image


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
        """Process a virtual try-on request using Workers AI.

        Args:
            user_image_bytes: The user's photo as bytes
            garment_image_url: URL of the garment/product image
            product_id: Product ID being tried on
            user_id: User ID making the request

        Returns:
            dict with status and result image URL
        """
        try:
            # Validate input image
            if not self._validate_image(user_image_bytes):
                return {
                    "status": "failed",
                    "error": "Invalid image format. Please upload a JPEG or PNG file.",
                }

            # Resize user image to optimal size for the model
            processed_image = self._preprocess_image(user_image_bytes)

            # Call Workers AI VTON model
            # pruna/p-image-try-on takes person image and garment image
            result = await self.ai.run(
                "@cf/pruna/p-image-try-on",
                {
                    "person_image": base64.b64encode(processed_image).decode("utf-8"),
                    "garment_image": garment_image_url,
                },
            )

            if result and "image" in result:
                # Convert result to bytes and store in R2
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
        try:
            key = f"vton/results/{user_id}/{product_id}_{int(__import__('time').time())}.jpg"

            # Upload to R2
            await self.env.R2.put(
                key=key,
                body=image_bytes,
                http_metadata={"contentType": "image/jpeg"},
            )

            # Return the public URL
            bucket_name = os.getenv("R2_BUCKET", "r2-thelineone01")
            return f"https://{bucket_name}.{os.getenv('R2_ACCOUNT_ID')}.r2.dev/{key}"

        except Exception as e:
            raise Exception(f"Failed to store result image: {str(e)}")

    async def store_user_image(self, image_bytes: bytes, user_id: str) -> str:
        """Store user uploaded image in R2."""
        try:
            key = f"vton/uploads/{user_id}/{int(__import__('time').time())}.jpg"

            await self.env.R2.put(
                key=key,
                body=image_bytes,
                http_metadata={"contentType": "image/jpeg"},
            )

            bucket_name = os.getenv("R2_BUCKET", "r2-thelineone01")
            return f"https://{bucket_name}.{os.getenv('R2_ACCOUNT_ID')}.r2.dev/{key}"

        except Exception as e:
            raise Exception(f"Failed to store user image: {str(e)}")

    def _validate_image(self, image_bytes: bytes) -> bool:
        """Validate that the uploaded file is a valid image."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()
            return True
        except Exception:
            return False

    def _preprocess_image(self, image_bytes: bytes, max_size: int = 1024) -> bytes:
        """Preprocess image for optimal VTON results."""
        try:
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Resize if too large
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size, Image.LANCZOS)

            # Save to bytes
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=90)
            return buffer.getvalue()

        except Exception:
            return image_bytes
