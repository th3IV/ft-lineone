from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class ProductDTO:
    external_id: str
    store: str
    name: str
    description: str
    price: float
    currency: str
    original_url: str
    image_urls: List[str] = field(default_factory=list)
    category: str = ""
    sizes: List[str] = field(default_factory=list)
    colors: List[str] = field(default_factory=list)
    availability: bool = True

    def to_dict(self) -> dict:
        return asdict(self)
