import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.local_storage import LocalStorage
from app.services.try_on_service import TryOnService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/try-on", tags=["try-on"])

try_on_service = TryOnService()
storage = LocalStorage()


class TryOnRequest(BaseModel):
    user_image_url: str
    product_image_url: str
    user_id: str = ""


@router.post("")
async def create_try_on(
    body: TryOnRequest | None = None,
    user_image: UploadFile | None = File(None),
    product_image_url: str | None = Form(None),
    user_id: str | None = Form(None),
) -> dict[str, Any]:
    if body:
        u_url = body.user_image_url
        p_url = body.product_image_url
        uid = body.user_id
    elif user_image and product_image_url:
        image_bytes = await user_image.read()
        filename = storage.save_image(image_bytes)
        u_url = storage.get_url(filename)
        p_url = product_image_url
        uid = user_id or ""
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide JSON body (user_image_url, product_image_url) or multipart (user_image file, product_image_url)",
        )
    job = await try_on_service.process_try_on(u_url, p_url)
    return job


@router.get("/{job_id}/status")
async def get_job_status(job_id: str) -> dict:
    status = try_on_service.get_job_status(job_id)
    if status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.get("/{job_id}/result")
async def get_job_result(job_id: str) -> dict:
    status = try_on_service.get_job_status(job_id)
    if status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job is {status['status']}")
    return {"job_id": job_id, "result_url": status["result_url"]}
