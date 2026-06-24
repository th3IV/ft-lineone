from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Any


class RawProduct(BaseModel):
    external_id: str
    store: str
    name: str
    price: float
    currency: str = "USD"
    image_url: HttpUrl
    category: str = ""
    sizes: List[str] = []
    colors: List[str] = []
    description: str = ""
    product_url: Optional[HttpUrl] = None


class ValidationResult(BaseModel):
    valid: bool
    reason: str
    warnings: List[str] = []
    cleaned_product: Optional[RawProduct] = None


class ValidateProductInput(BaseModel):
    product: RawProduct


class ValidateProductOutput(BaseModel):
    valid: bool
    reason: str
    warnings: List[str] = []
    cleaned_product: Optional[RawProduct] = None