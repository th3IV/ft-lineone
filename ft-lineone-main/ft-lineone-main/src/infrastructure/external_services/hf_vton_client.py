import httpx
import asyncio
from typing import Dict, Any, Optional
from src.core.config import settings


class HFVTONClient:
    def __init__(
        self,
        space_url: str | None = None,
        hf_token: str | None = None,
    ):
        self._space_url = (space_url or settings.HF_SPACE_URL).rstrip("/")
        self._headers = {}
        if hf_token or settings.HF_TOKEN:
            self._headers["Authorization"] = f"Bearer {hf_token or settings.HF_TOKEN}"

    async def submit_try_on(
        self,
        user_image_b64: str,
        garment_image_b64: str,
    ) -> str:
        """
        Envía job a HF Space. Retorna hf_job_id para polling.
        Formato típico Gradio API: POST /run/predict
        """
        async with httpx.AsyncClient(timeout=60.0, headers=self._headers) as client:
            payload = {
                "data": [
                    f"data:image/png;base64,{user_image_b64}",
                    f"data:image/png;base64,{garment_image_b64}",
                    "",
                ]
            }
            response = await client.post(
                f"{self._space_url}/run/predict",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            event_id = data.get("event_id") or data.get("job_id")
            if not event_id:
                raise ValueError(f"Unexpected HF response: {data}")
            return event_id

    async def get_status(self, job_id: str) -> Dict[str, Any]:
        """
        Polling de status. Retorna dict con status, output_url, error.
        """
        async with httpx.AsyncClient(timeout=30.0, headers=self._headers) as client:
            response = await client.get(
                f"{self._space_url}/queue/status",
                params={"job_id": job_id},
            )

            if response.status_code == 404:
                return {"status": "not_found", "error": "Job not found"}

            response.raise_for_status()
            data = response.json()

            status = data.get("status", "unknown")

            if status == "COMPLETED":
                output = data.get("output", {})
                output_data = output.get("data", [])
                output_url = output_data[0] if output_data else None
                return {
                    "status": "completed",
                    "output_url": output_url,
                }

            elif status in ("FAILED", "ERROR"):
                return {
                    "status": "failed",
                    "error": data.get("error", "HF job failed"),
                }

            return {"status": "processing"}

    async def get_result(self, job_id: str) -> Dict[str, Any]:
        """
        Obtiene resultado final cuando está completado.
        """
        async with httpx.AsyncClient(timeout=30.0, headers=self._headers) as client:
            response = await client.get(
                f"{self._space_url}/run/{job_id}/outputs",
            )
            response.raise_for_status()
            return response.json()