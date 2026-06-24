from pydantic import BaseModel, HttpUrl
from typing import Optional, List


class UserBodyMeasurements(BaseModel):
    height: Optional[int] = None
    weight: Optional[int] = None
    bust: Optional[int] = None
    waist: Optional[int] = None
    hip: Optional[int] = None
    size_top: Optional[str] = None
    size_bottom: Optional[str] = None


class UserProfile(BaseModel):
    user_id: str
    body_measurements: UserBodyMeasurements = UserBodyMeasurements()
    preferences: List[str] = []
    favorite_colors: List[str] = []
    price_range: Optional[dict] = None
    style_notes: str = ""


class ProductColor(BaseModel):
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


class ProductSummary(BaseModel):
    external_id: str
    store: str
    slug: str
    name: str
    description: str
    price: float
    currency: str
    category: str
    subcategory: str
    sizes: List[str] = []
    colors: List[ProductColor] = []
    images: List[ProductImage] = []
    attributes: ProductAttributes = ProductAttributes()


class RecommendationItem(BaseModel):
    product_id: str
    score: float
    reason: str
    matched_attributes: List[str] = []


class RecommendProductsInput(BaseModel):
    user_profile: UserProfile
    products: List[ProductSummary]
    limit: int = 10


class RecommendProductsOutput(BaseModel):
    recommendations: List[RecommendationItem]