from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel


class VTONStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VTONResult(BaseModel):
    id: str | None = None
    user_id: str
    product_id: str
    input_image_url: str
    output_image_url: str = ""
    status: VTONStatus = VTONStatus.PENDING
    created_at: datetime = datetime.now(timezone.utc)
