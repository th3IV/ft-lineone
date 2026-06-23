import asyncio
import base64
import httpx
import uuid
from src.application.agents.skills.virtual_try_on.schema import VTONSkillInput, VTONSkillOutput
from src.infrastructure.external_services.hf_vton_client import HFVTONClient
from src.infrastructure.external_services.grok_client import GrokClient
from src.infrastructure.external_services.cloudinary_client import CloudinaryClient
from src.infrastructure.external_services.genlook_client import GenlookVTONClient


class VTONSkill:
    def __init__(
        self,
        grok_client: GrokClient | None = None,
        hf_client: HFVTONClient | None = None,
        cloudinary_client: CloudinaryClient | None = None,
        genlook_client: GenlookVTONClient | None = None,
    ):
        self._grok = grok_client
        self._hf = hf_client
        self._cloudinary = cloudinary_client
        self._genlook = genlook_client

    async def execute(
        self,
        input_data: VTONSkillInput,
        user_image_bytes: bytes | None = None,
    ) -> VTONSkillOutput:
        job_id = input_data.job_id or str(uuid.uuid4())

        try:
            # 1. Genlook (primario - real VTON, rápido, económico)
            if self._genlook and user_image_bytes:
                result_url = await self._process_with_genlook(
                    job_id=job_id,
                    user_image_bytes=user_image_bytes,
                    garment_image_url=str(input_data.product_image_url),
                    product_id=input_data.product_id,
                    product_name="",
                )
            # 2. Grok Imagine (fallback - no es VTON real pero genera imagen)
            elif self._grok and self._grok._available:
                result_url = await self._process_with_grok(
                    job_id=job_id,
                    user_image_url=str(input_data.user_image_url),
                    garment_image_url=str(input_data.product_image_url),
                )
            # 3. HF Space (último fallback - lento pero gratis)
            elif self._hf:
                result_url = await self._process_with_hf(
                    job_id=job_id,
                    user_image_url=str(input_data.user_image_url),
                    garment_image_url=str(input_data.product_image_url),
                )
            else:
                return VTONSkillOutput(
                    job_id=job_id,
                    status="failed",
                    error="No hay cliente VTON disponible (Genlook, Grok ni HF)",
                )

            return VTONSkillOutput(
                job_id=job_id,
                status="completed",
                result_url=result_url,
            )

        except Exception as e:
            # Fallback a HF si Genlook falló
            if self._genlook and self._hf:
                try:
                    result_url = await self._process_with_hf(
                        job_id=job_id,
                        user_image_url=str(input_data.user_image_url),
                        garment_image_url=str(input_data.product_image_url),
                    )
                    return VTONSkillOutput(
                        job_id=job_id,
                        status="completed",
                        result_url=result_url,
                    )
                except Exception as hf_e:
                    return VTONSkillOutput(
                        job_id=job_id,
                        status="failed",
                        error=f"Genlook: {e} | HF: {hf_e}",
                    )

            return VTONSkillOutput(
                job_id=job_id,
                status="failed",
                error=str(e),
            )

    async def _process_with_genlook(
        self,
        job_id: str,
        user_image_bytes: bytes,
        garment_image_url: str,
        product_id: str,
        product_name: str,
    ) -> str:
        result = await self._genlook.submit_try_on(
            user_image_bytes=user_image_bytes,
            product_id=product_id,
            product_image_url=garment_image_url,
            product_name=product_name,
        )
        generation_id = result["generationId"]
        result_url = await self._genlook.poll_result(generation_id)
        return result_url

    async def _process_with_grok(
        self,
        job_id: str,
        user_image_url: str,
        garment_image_url: str,
    ) -> str:
        prompt = (
            "A photorealistic photo of a person wearing this exact garment. "
            "The garment fits naturally on the person's body, preserving its "
            "original color, pattern, texture, and shape accurately. "
            "Natural lighting, studio quality, fashion photography style."
        )
        result = await self._grok.generate_image(
            prompt=prompt,
            image_urls=[user_image_url, garment_image_url],
            aspect_ratio="3:4",
        )
        return result["url"]

    async def _process_with_hf(
        self,
        job_id: str,
        user_image_url: str,
        garment_image_url: str,
    ) -> str:
        user_image_b64 = await self._download_and_encode(user_image_url)
        garment_image_b64 = await self._download_and_encode(garment_image_url)

        hf_job_id = await self._hf.submit_try_on(user_image_b64, garment_image_b64)
        result_url = await self._poll_and_upload(job_id, hf_job_id)
        return result_url

    async def _download_and_encode(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return base64.b64encode(response.content).decode("utf-8")

    async def _poll_and_upload(self, job_id: str, hf_job_id: str) -> str:
        max_wait = 300
        poll_interval = 5
        waited = 0

        while waited < max_wait:
            status = await self._hf.get_status(hf_job_id)

            if status["status"] == "completed":
                result_url = status.get("output_url")
                if not result_url:
                    raise ValueError("HF job completed but no output URL")

                image_bytes = await self._download_image(result_url)
                folder = f"vton/results/{job_id}"
                upload_result = self._cloudinary.upload_image(
                    image_bytes=image_bytes,
                    folder=folder,
                    public_id=f"{job_id}_result",
                )
                return self._cloudinary.generate_url(
                    public_id=upload_result["public_id"],
                    transformation={"quality": "auto", "fetch_format": "auto"},
                )

            elif status["status"] == "failed":
                raise RuntimeError(f"HF VTON failed: {status.get('error', 'Unknown error')}")

            await asyncio.sleep(poll_interval)
            waited += poll_interval

        raise TimeoutError(f"VTON job {hf_job_id} timed out after {max_wait}s")

    async def _download_image(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
