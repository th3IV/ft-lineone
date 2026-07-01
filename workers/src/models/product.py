import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    store: str = Field(..., min_length=1, max_length=50)
    price: float = Field(..., gt=0)
    currency: str = Field(default="CLP", max_length=3)
    category: str = ""
    description: str = ""
    original_url: str = ""


class ProductCreate(ProductBase):
    external_id: str = Field(..., min_length=1)
    image_urls: list[str] = []
    sizes: list[str] = []
    colors: list[str] = []
    availability: bool = True


class ProductResponse(ProductBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    image_url: Optional[str] = None
    sizes: list[str] = []
    colors: list[str] = []
    availability: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    products: list[ProductResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class ProductFilter(BaseModel):
    store: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    query: Optional[str] = None
    gender: Optional[str] = None
    clothing_type: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    page: int = 1
    limit: int = 20
