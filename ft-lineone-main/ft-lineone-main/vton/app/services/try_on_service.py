import asyncio
import logging
import uuid
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from PIL import Image

from app.models.diffusion_model import DiffusionModel
from app.services.image_processor import ImageProcessor
from app.services.s3_connector import S3Connector

logger = logging.getLogger(__name__)


class TryOnService:
    def __init__(self):
        self.model = DiffusionModel()
        self.processor = ImageProcessor()
        self.s3 = S3Connector()
        self._jobs: dict[str, dict[str, Any]] = {}

    async def process_try_on(
        self, user_image_bytes: bytes, product_image_url: str, job_id: str | None = None
    ) -> dict:
        job_id = job_id or str(uuid.uuid4())
        self._jobs[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "progress": 0,
            "result_url": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }

        try:
            self._jobs[job_id]["progress"] = 10

            user_image = Image.open(BytesIO(user_image_bytes)).convert("RGB")
            clothing_bytes = await asyncio.to_thread(
                self.s3.download_image, product_image_url
            )
            clothing_image = Image.open(BytesIO(clothing_bytes)).convert("RGB")

            self._jobs[job_id]["progress"] = 30

            user_image, clothing_image = self.processor.align_pose(
                user_image, clothing_image
            )

            self._jobs[job_id]["progress"] = 50

            result_image = await asyncio.to_thread(
                self.model.generate_try_on, user_image, clothing_image
            )

            self._jobs[job_id]["progress"] = 80

            result_bytes = self.processor.encode_image(result_image, "PNG")

            result_key = f"results/{job_id}/output.png"
            result_url = await asyncio.to_thread(
                self.s3.upload_image, result_bytes, result_key
            )

            self._jobs[job_id].update(
                {
                    "status": "completed",
                    "progress": 100,
                    "result_url": result_url,
                }
            )
        except Exception as exc:
            logger.exception("Try-on processing failed for job %s", job_id)
            self._jobs[job_id].update(
                {"status": "failed", "error": str(exc)}
            )

        return self._jobs[job_id]

    def get_job_status(self, job_id: str) -> dict:
        job = self._jobs.get(job_id)
        if not job:
            return {"job_id": job_id, "status": "not_found"}
        return dict(job)

    def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job["status"] in ("processing", "pending"):
            self._jobs[job_id]["status"] = "cancelled"
            return True
        return False
