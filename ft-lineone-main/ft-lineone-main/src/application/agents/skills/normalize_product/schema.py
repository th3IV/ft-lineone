from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime


class ColorInfo(BaseModel):
    name: str


class ProductImage(BaseModel):
    url: HttpUrl
    width: Optional[int] = None
    height: Optional[int] = None
    is_primary: bool = False


class ProductAttributes(BaseModel):
    fit: Optional[str] = None
    material: Optional[str] = None
    occasion: Optional[str] = None
    season: Optional[str] = None


class NormalizedProduct(BaseModel):
    external_id: str
    store: str
    slug: str
    name: str
    description: str
    price: float
    currency: str
    category: str
    subcategory: str = ""
    sizes: List[str] = []
    colors: List[ColorInfo] = []
    images: List[ProductImage] = []
    attributes: ProductAttributes = ProductAttributes()
    product_url: HttpUrl
    scraped_at: datetime


class NormalizeProductInput(BaseModel):
    product: dict


class NormalizeProductOutput(BaseModel):
    normalized: NormalizedProduct