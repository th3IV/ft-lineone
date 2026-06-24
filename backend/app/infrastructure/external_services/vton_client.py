from uuid import uuid4

import httpx

from app.core.config import settings
from app.domain.models.vton_result import VTONResult, VTONStatus


class VTONClient:
    def __init__(self, base_url: str | None = None):
        self._base_url = base_url or settings.VTON_API_URL
        self._base_url = base_url

    async def request_try_on(self, user_image_url: str, product_image_url: str) -> VTONResult:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/vton/try-on",
                json={
                    "user_image_url": user_image_url,
                    "product_image_url": product_image_url,
                },
                timeout=300.0,
            )
            response.raise_for_status()
            data = response.json()
            return VTONResult(
                id=data.get("id", str(uuid4())),
                user_id=data.get("user_id", ""),
                product_id=data.get("product_id", ""),
                input_image_url=user_image_url,
                output_image_url=data.get("output_image_url", ""),
                status=VTONStatus(data.get("status", "pending")),
            )

    async def get_result(self, job_id: str) -> VTONResult | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/vton/result/{job_id}",
                timeout=30.0,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            return VTONResult(
                id=data.get("id", job_id),
                user_id=data.get("user_id", ""),
                product_id=data.get("product_id", ""),
                input_image_url=data.get("input_image_url", ""),
                output_image_url=data.get("output_image_url", ""),
                status=VTONStatus(data.get("status", "pending")),
            )
