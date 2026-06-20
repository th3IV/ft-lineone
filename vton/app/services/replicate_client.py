import os
import logging
import replicate
from typing import Optional

logger = logging.getLogger(__name__)

class ReplicateClient:
    def __init__(self, api_token: Optional[str] = None, model_name: Optional[str] = None):
        self.api_token = api_token or os.getenv("REPLICATE_API_TOKEN")
        self.model_name = model_name or os.getenv("REPLICATE_MODEL", "cuuupid/idm-vton")

        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN is not set")

        os.environ["REPLICATE_API_TOKEN"] = self.api_token

    def generate_try_on(self, user_image_url: str, product_image_url: str) -> str:
        """
        Calls Replicate API (IDM-VTON) to generate a Virtual Try-On image.
        Inputs: model_image (person), garment_image (clothing).
        Output: ["https://..."] array, returns first element.
        """
        try:
            logger.info("Requesting try-on from Replicate model %s", self.model_name)

            output = replicate.run(
                self.model_name,
                input={
                    "model_image": user_image_url,
                    "garment_image": product_image_url,
                }
            )

            if isinstance(output, list) and len(output) > 0:
                return output[0]
            return str(output)

        except Exception as e:
            logger.error("Replicate API error: %s", e)
            raise
