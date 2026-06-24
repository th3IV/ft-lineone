import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import replicate

from app.services.local_storage import LocalStorage

logger = logging.getLogger(__name__)

REPLICATE_MODEL = os.getenv("REPLICATE_MODEL", "cuuupid/idm-vton")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")


class TryOnService:
    def __init__(self):
        self.storage = LocalStorage()
        self._jobs: dict[str, dict[str, Any]] = {}

    async def process_try_on(
        self,
        user_image_url: str,
        product_image_url: str,
        job_id: str | None = None,
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
            self._jobs[job_id]["progress"] = 30
            if not REPLICATE_API_TOKEN:
                raise ValueError("REPLICATE_API_TOKEN is not configured")

            client = replicate.Client(api_token=REPLICATE_API_TOKEN)
            output = client.run(
                REPLICATE_MODEL,
                input={
                    "human_image": user_image_url,
                    "cloth_image": product_image_url,
                },
            )
            self._jobs[job_id]["progress"] = 80

            if output and hasattr(output, "url"):
                result_url = str(output.url)
            elif isinstance(output, list) and len(output) > 0:
                result_url = str(output[0])
            elif isinstance(output, str):
                result_url = output
            else:
                result_url = str(output)

            self._jobs[job_id].update(
                {
                    "status": "completed",
                    "progress": 100,
                    "result_url": result_url,
                }
            )
        except Exception as exc:
            logger.exception("Try-on processing failed for job %s", job_id)
            self._jobs[job_id].update({"status": "failed", "error": str(exc)})
        return self._jobs[job_id]

    def get_job_status(self, job_id: str) -> dict:
        job = self._jobs.get(job_id)
        if not job:
            return {"job_id": job_id, "status": "not_found"}
        return dict(job)
