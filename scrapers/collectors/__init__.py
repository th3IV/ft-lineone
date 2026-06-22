from .falabella_scraper import FalabellaScraper
from .ripley_scraper import RipleyScraper
from .paris_scraper import ParisScraper
from .maui_scraper import MauiScraper
from .zara_scraper import ZaraScraper

__all__ = [
    "FalabellaScraper",
    "RipleyScraper",
    "ParisScraper",
    "MauiScraper",
    "ZaraScraper",
]

SCRAPER_REGISTRY: dict[str, type] = {
    "falabella": FalabellaScraper,
    "ripley": RipleyScraper,
    "paris": ParisScraper,
    "maui": MauiScraper,
    "zara": ZaraScraper,
}


def get_scraper(store: str):
    cls = SCRAPER_REGISTRY.get(store.lower())
    if cls:
        return cls()
    raise ValueError(f"Unknown store: {store}. Available: {list(SCRAPER_REGISTRY.keys())}")


def run_scraper(store: str, category: str = "ropa", max_items: int = 20) -> list[dict]:
    scraper = get_scraper(store)
    products = scraper.scrape(category=category, max_items=max_items)
    return [p.to_dict() for p in products]
