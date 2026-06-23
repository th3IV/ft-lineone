import httpx
from src.application.agents.skills.process_product_image.schema import (
    ProcessImageInput,
    ProcessImageOutput,
    ProductImage,
)
from src.infrastructure.external_services.cloudinary_client import CloudinaryClient


class ProcessProductImageSkill:
    def __init__(self, cloudinary_client: CloudinaryClient):
        self._cloudinary = cloudinary_client
        self._skill_name = "process_product_image"

    async def execute(self, input_data: ProcessImageInput) -> ProcessImageOutput:
        image_bytes = await self._download_image(str(input_data.image_url))
        if not image_bytes:
            raise ValueError(f"Failed to download image from {input_data.image_url}")

        folder = f"products/{input_data.store}/{input_data.external_id}"
        upload_result = await self._cloudinary.upload_image(
            image_bytes=image_bytes,
            folder=folder,
            public_id=f"{input_data.external_id}_main",
        )

        transformations = [
            ("thumbnail", {"width": 200, "height": 200, "crop": "fill"}),
            ("card", {"width": 400, "height": 400, "crop": "fill"}),
            ("detail", {"width": 800, "crop": "limit"}),
            ("original", {}),
        ]

        images = []
        for i, (name, params) in enumerate(transformations):
            url = self._cloudinary.generate_url(
                public_id=upload_result["public_id"],
                transformation=params,
            )
            images.append(
                ProductImage(
                    url=url,
                    width=params.get("width"),
                    height=params.get("height"),
                    is_primary=(i == 0 and input_data.is_primary),
                )
            )

        return ProcessImageOutput(images=images)

    async def _download_image(self, url: str) -> bytes | None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
                if not content_type.startswith("image/"):
                    return None
                return response.content
            except Exception:
                return None