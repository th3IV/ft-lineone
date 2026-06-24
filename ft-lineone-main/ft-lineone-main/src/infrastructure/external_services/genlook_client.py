import json
import httpx
import asyncio
from typing import Dict, Any
from src.core.config import settings

GENLOOK_BASE = "https://api.genlook.app/tryon/v1"


class GenlookVTONClient:
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or settings.GENLOOK_API_KEY
        self._headers = {"x-api-key": self._api_key}

    async def submit_try_on(
        self,
        user_image_bytes: bytes,
        product_id: str,
        product_image_url: str,
        product_name: str = "",
        product_description: str = "",
        user_image_filename: str = "user.jpg",
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            data_payload = {
                "products": [
                    {
                        "externalId": product_id,
                        "title": product_name or "Product",
                        "description": product_description or product_name or "Product",
                        "images": [{"source": {"url": product_image_url}}],
                    }
                ],
                "person": {
                    "image": {"source": {"fileKey": "person"}}
                },
            }
            files = {
                "data": (None, json.dumps(data_payload), "application/json"),
                "person": (user_image_filename, user_image_bytes, "image/jpeg"),
            }

            response = await client.post(
                f"{GENLOOK_BASE}/try-on",
                headers=self._headers,
                files=files,
            )

            if response.status_code == 402:
                raise RuntimeError(
                    "Genlook: insufficient credits. Go to https://app.genlook.app to top up."
                )
            if response.status_code == 404:
                raise RuntimeError(
                    f"Genlook: product not found - {response.text}"
                )

            response.raise_for_status()
            data = response.json()
            return data

    async def poll_result(self, generation_id: str, timeout_s: int = 180) -> str:
        deadline = asyncio.get_event_loop().time() + timeout_s
        async with httpx.AsyncClient(timeout=10.0) as client:
            while True:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    raise TimeoutError(
                        f"Genlook: generation {generation_id} timed out after {timeout_s}s"
                    )

                response = await client.get(
                    f"{GENLOOK_BASE}/generations/{generation_id}",
                    headers=self._headers,
                )
                response.raise_for_status()
                data = response.json()
                status = data["status"]

                if status == "COMPLETED":
                    return data["resultImageUrl"]
                if status == "FAILED":
                    raise RuntimeError(
                        f"Genlook: generation failed - {data.get('errorMessage', 'Unknown error')}"
                    )

                await asyncio.sleep(2)
