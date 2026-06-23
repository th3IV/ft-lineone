import cloudinary
import cloudinary.uploader
import cloudinary.utils
from typing import Optional
from src.core.config import settings


class CloudinaryClient:
    def __init__(
        self,
        cloud_name: str | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
    ):
        cloudinary.config(
            cloud_name=cloud_name or settings.CLOUDINARY_CLOUD_NAME,
            api_key=api_key or settings.CLOUDINARY_API_KEY,
            api_secret=api_secret or settings.CLOUDINARY_API_SECRET,
            secure=True,
        )

    def upload_image(
        self,
        image_bytes: bytes,
        folder: str,
        public_id: str,
    ) -> dict:
        result = cloudinary.uploader.upload(
            image_bytes,
            folder=folder,
            public_id=public_id,
            overwrite=True,
            resource_type="image",
            quality="auto",
            fetch_format="auto",
        )
        return result

    def generate_url(self, public_id: str, transformation: dict | None = None) -> str:
        params = {"secure": True}
        if transformation:
            params["transformation"] = [transformation]
        return cloudinary.utils.cloudinary_url(public_id, **params)[0]

    def delete_image(self, public_id: str) -> dict:
        return cloudinary.uploader.destroy(public_id, resource_type="image")