from datetime import datetime, timezone

from pydantic import BaseModel


class PriceHistory(BaseModel):
    id: str | None = None
    product_id: str
    external_id: str = ""
    store: str
    price: float
    currency: str = "USD"
    scraped_at: datetime = datetime.now(timezone.utc)
