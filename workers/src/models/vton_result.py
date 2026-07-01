import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VtonStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VtonRequest(BaseModel):
    product_id: str = Field(..., min_length=1)


class VtonResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    product_id: str
    status: VtonStatus = VtonStatus.PENDING
    input_image_url: Optional[str] = None
    output_image_url: Optional[str] = None
    garment_image_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VtonHistoryResponse(BaseModel):
    results: list[VtonResult]
    total: int
