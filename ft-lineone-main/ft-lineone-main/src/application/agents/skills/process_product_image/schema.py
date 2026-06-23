from pydantic import BaseModel, HttpUrl
from typing import Optional, List


class ProductImage(BaseModel):
    url: HttpUrl
    width: Optional[int] = None
    height: Optional[int] = None
    is_primary: bool = False


class ProcessImageInput(BaseModel):
    external_id: str
    store: str
    image_url: HttpUrl
    is_primary: bool = True


class ProcessImageOutput(BaseModel):
    images: List[ProductImage]