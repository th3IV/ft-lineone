import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.services.replicate_client import ReplicateClient
from app.services.local_storage import LocalStorage

logger = logging.getLogger(__name__)


class TryOnService:
    def __init__(self, storage: LocalStorage, replicate_client: ReplicateClient):
        self.storage = storage
        self.replicate = replicate_client
        self._jobs: dict[str, dict[str, Any]] = {}

    async def process_try_on(
        self,
        product_image_url: str,
        user_image_bytes: bytes | None = None,
        user_image_url: str = "",
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
            self._jobs[job_id]["progress"] = 10

            if user_image_url:
                user_url = user_image_url
            elif user_image_bytes:
                user_key = f"vton/users/{job_id}_user.png"
                user_url = self.storage.save_image(user_image_bytes, user_key)
            else:
                raise ValueError("No user image provided")

            self._jobs[job_id]["progress"] = 30

            result_url = self.replicate.generate_try_on(user_url, product_image_url)

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
