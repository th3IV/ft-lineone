"""Virtual Try-On service using Cloudflare Workers AI + Pruna P-Image-Try-On."""

import base64
import time


MODEL = "pruna/p-image-try-on"


class VtonService:
    """VTON service using Pruna P-Image-Try-On via Workers AI."""

    def __init__(self, env):
        self.env = env
        self.ai = env.AI

    async def process_try_on(
        self,
        user_image_url: str,
        garment_image_url: str,
        product_id: str,
        user_id: str,
    ) -> dict:
        """Process a virtual try-on request using Pruna P-Image-Try-On.

        Args:
            user_image_url: Public URL of the user's photo (from R2).
            garment_image_url: Public URL of the garment image.
            product_id: Product ID.
            user_id: User ID.

        Returns:
            dict with status and image_bytes (raw JPEG).
        """
        try:
            model_input = {
                "person_image": user_image_url,
                "garment_images": [garment_image_url],
                "output_format": "jpg",
                "preserve_input_size": True,
            }

            gateway_id = getattr(self.env, "CLOUDFLARE_AI_GATEWAY_ID", None)
            options = {}
            if gateway_id:
                options["gateway"] = {"id": gateway_id}

            result = await self.ai.run(MODEL, model_input, options)

            image_url = None
            if result:
                if isinstance(result, dict):
                    inner = result.get("result") or result
                    if isinstance(inner, dict):
                        image_url = inner.get("image")
                    if not image_url:
                        image_url = result.get("image")

            if not image_url:
                error_msg = "Pruna model did not return an image."
                if result and isinstance(result, dict):
                    errors = result.get("errors") or []
                    messages = result.get("messages") or []
                    if errors:
                        error_msg = errors[0].get("message", error_msg)
                    elif messages:
                        error_msg = messages[0].get("message", error_msg)
                return {"status": "failed", "error": error_msg}

            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                img_resp = await client.get(image_url)
                if img_resp.status_code != 200:
                    return {
                        "status": "failed",
                        "error": f"Failed to fetch result image: HTTP {img_resp.status_code}",
                    }
                image_bytes = img_resp.content

            return {
                "status": "completed",
                "image_bytes": image_bytes,
                "content_type": "image/jpeg",
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": f"VTON processing failed: {str(e)}",
            }


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
