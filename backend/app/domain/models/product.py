from datetime import datetime, timezone

from pydantic import BaseModel


import re
import unicodedata


def normalize_product_name(name: str) -> str:
    text = name.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\b(en oferta|envio gratis|outlet|nuevo|limited|exclusivo)\b", "", text)
    text = re.sub(r"\b(s|m|l|xl|xxl|xs|unico|unique)\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class Product(BaseModel):
    id: str | None = None
    external_id: str
    store: str
    name: str
    normalized_name: str = ""
    description: str = ""
    price: float
    currency: str = "USD"
    image_url: str = ""
    category: str = ""
    sizes: list[str] = []
    colors: list[str] = []
    scraped_at: datetime = datetime.now(timezone.utc)

    def model_post_init(self, __context):
        if not self.normalized_name:
            self.normalized_name = normalize_product_name(self.name)
