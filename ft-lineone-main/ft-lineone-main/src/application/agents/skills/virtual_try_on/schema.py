from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class VTONRequest(BaseModel):
    user_id: str
    user_image_url: HttpUrl
    product_id: str
    product_image_url: HttpUrl


class VTONResult(BaseModel):
    job_id: str
    status: str  # "completed" | "failed" | "processing"
    result_url: Optional[HttpUrl] = None
    error: Optional[str] = None
    created_at: datetime


class VTONSkillInput(BaseModel):
    user_id: str
    user_image_url: HttpUrl = "https://placeholder.genlook.app/placeholder.jpg"
    product_id: str
    product_image_url: HttpUrl
    job_id: str | None = None


class VTONSkillOutput(BaseModel):
    job_id: str
    status: str
    result_url: Optional[HttpUrl] = None
    error: Optional[str] = None