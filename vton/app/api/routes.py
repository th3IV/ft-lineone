import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.replicate_client import ReplicateClient
from app.services.local_storage import LocalStorage
from app.services.try_on_service import TryOnService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/try-on", tags=["try-on"])

storage = LocalStorage()
replicate_client = ReplicateClient()
try_on_service = TryOnService(storage=storage, replicate_client=replicate_client)


class StatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int | None = None
    result_url: str | None = None
    error: str | None = None


class ResultResponse(BaseModel):
    job_id: str
    result_url: str


class TryOnRequest(BaseModel):
    user_image_url: str
    product_image_url: str
    product_id: str = ""
    user_id: str = ""


@router.post("")
async def create_try_on(
    payload: TryOnRequest | None = None,
    user_image: UploadFile | None = File(None),
    product_image_url: str = Form(""),
    product_id: str = Form(""),
    user_id: str = Form(""),
) -> dict[str, Any]:
    if payload:
        job = await try_on_service.process_try_on(
            user_image_bytes=None,
            product_image_url=payload.product_image_url,
            user_image_url=payload.user_image_url,
        )
    elif user_image:
        image_bytes = await user_image.read()
        job = await try_on_service.process_try_on(
            user_image_bytes=image_bytes,
            product_image_url=product_image_url,
        )
    else:
        raise HTTPException(status_code=400, detail="Provide user_image (file) or JSON body with user_image_url")
    return job


@router.get("/{job_id}/status", response_model=StatusResponse)
async def get_job_status(job_id: str) -> StatusResponse:
    status = try_on_service.get_job_status(job_id)
    if status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    return StatusResponse(**status)


@router.get("/{job_id}/result", response_model=ResultResponse)
async def get_job_result(job_id: str) -> ResultResponse:
    status = try_on_service.get_job_status(job_id)
    if status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job is {status['status']}")
    return ResultResponse(job_id=job_id, result_url=status["result_url"])


@router.post("/{job_id}/retry")
async def retry_job(job_id: str) -> dict[str, Any]:
    status = try_on_service.get_job_status(job_id)
    if status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    if status["status"] != "failed":
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
    return {"job_id": job_id, "detail": "Retry not yet implemented"}
