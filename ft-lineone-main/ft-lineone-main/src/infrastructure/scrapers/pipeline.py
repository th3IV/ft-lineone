from typing import List, Dict, Any
from src.infrastructure.scrapers.zara_scraper import ZaraScraper
from src.infrastructure.scrapers.hm_scraper import HMScraper
from src.infrastructure.scrapers.base_scraper import BaseScraper
from src.application.agents.skills.validate_product.service import ValidateProductSkill
from src.application.agents.skills.normalize_product.service import NormalizeProductSkill
from src.application.agents.skills.process_product_image.service import ProcessProductImageSkill
from src.infrastructure.database.mongodb.repositories import MongoProductRepository
from src.infrastructure.external_services.grok_client import GrokClient
from src.infrastructure.external_services.cloudinary_client import CloudinaryClient
from src.core.config import settings
from src.infrastructure.scrapers.falabella_scraper import FalabellaScraper
from src.infrastructure.scrapers.ripley_scraper import RipleyScraper
from src.infrastructure.scrapers.paris_scraper import ParisScraper
from src.infrastructure.scrapers.maui_scraper import MauiScraper


class ScraperPipeline:
    CATEGORIES = [
        "woman_tshirts",
        "woman_dresses",
        "woman_pants",
        "woman_jackets",
        "man_tshirts",
        "man_shirts",
        "man_pants",
        "man_jackets",
    ]

    def __init__(
        self,
        grok_client: GrokClient | None = None,
        cloudinary_client: CloudinaryClient | None = None,
        mongo_repo: MongoProductRepository | None = None,
    ):
        self._grok = grok_client or GrokClient()
        self._cloudinary = cloudinary_client or CloudinaryClient()
        self._repo = mongo_repo or MongoProductRepository()

        self._validate_skill = ValidateProductSkill(self._grok)
        self._normalize_skill = NormalizeProductSkill(self._grok)
        self._image_skill = ProcessProductImageSkill(self._cloudinary)

        self._scrapers: Dict[str, BaseScraper] = {
            "zara": ZaraScraper(),
            "hm": HMScraper(),
            "falabella": FalabellaScraper(),
            "ripley": RipleyScraper(),
            "paris": ParisScraper(),
            "maui": MauiScraper(),
        }

    def get_scraper(self, store: str) -> BaseScraper | None:
        return self._scrapers.get(store)

    async def run_scraper(self, store: str, categories: List[str] | None = None, max_per_category: int = 20) -> dict:
        scraper = self.get_scraper(store)
        if not scraper:
            return {"success": False, "error": f"Unknown store: {store}"}

        scraper.set_skills(
            validate=self._validate_skill,
            normalize=self._normalize_skill,
            image=self._image_skill,
            repo=self._repo,
        )

        categories = categories or self.CATEGORIES
        all_raw_products = []

        for category in categories:
            try:
                raw = await scraper.scrape_category(category, max_per_category)
                all_raw_products.extend(raw)
            except Exception as e:
                return {"success": False, "error": f"Scraping {category} failed: {e}"}

        result = await scraper.process_raw_products(all_raw_products)
        await scraper.close()

        return {"success": True, **result}

    async def run_all_stores(self, categories: List[str] | None = None, max_per_category: int = 20) -> dict:
        results = {}
        for store in self._scrapers:
            results[store] = await self.run_scraper(store, categories, max_per_category)
        return {"success": True, "results": results}

    async def close_all(self):
        for scraper in self._scrapers.values():
            await scraper.close()