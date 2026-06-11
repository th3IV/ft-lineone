from datetime import datetime, timezone

from pydantic import BaseModel


class Product(BaseModel):
    id: str | None = None
    external_id: str
    store: str
    name: str
    description: str = ""
    price: float
    currency: str = "USD"
    image_url: str = ""
    category: str = ""
    sizes: list[str] = []
    colors: list[str] = []
    scraped_at: datetime = datetime.now(timezone.utc)
