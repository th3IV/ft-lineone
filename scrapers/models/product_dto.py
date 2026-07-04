"""Product data transfer object for scraped products."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ProductDTO:
    external_id: str
    store: str
    name: str
    description: str = ""
    price: float = 0.0
    currency: str = "CLP"
    original_url: str = ""
    image_urls: List[str] = field(default_factory=list)
    category: str = ""
    sizes: List[str] = field(default_factory=list)
    colors: List[str] = field(default_factory=list)
    availability: bool = True
