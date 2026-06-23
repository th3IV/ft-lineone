from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.domain.models.vton_result import VTONResult, VTONStatus


class VTONCoordinator:
    def __init__(self):
        self._job_queue: dict[str, dict[str, Any]] = {}
        self._results: dict[str, VTONResult] = {}

    async def submit_job(self, user_id: str, product_id: str, image_url: str) -> dict:
        job_id = str(uuid4())
        result = VTONResult(
            id=job_id,
            user_id=user_id,
            product_id=product_id,
            input_image_url=image_url,
            status=VTONStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )
        self._results[job_id] = result
        self._job_queue[job_id] = {
            "job_id": job_id,
            "user_id": user_id,
            "product_id": product_id,
            "image_url": image_url,
            "status": VTONStatus.PENDING.value,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        return {"job_id": job_id, "status": VTONStatus.PENDING.value}

    async def check_job_status(self, job_id: str) -> dict:
        result = self._results.get(job_id)
        if not result:
            return {"error": "Job not found"}
        return {
            "job_id": job_id,
            "status": result.status.value,
            "output_image_url": result.output_image_url,
        }

    async def retry_failed(self) -> list[str]:
        retried = []
        for job_id, job in list(self._job_queue.items()):
            result = self._results.get(job_id)
            if result and result.status == VTONStatus.FAILED:
                result.status = VTONStatus.PENDING
                job["status"] = VTONStatus.PENDING.value
                retried.append(job_id)
        return retried
