from datetime import datetime, timezone

from app.domain.models.product import Product
from app.infrastructure.external_services.llm_client import LLMClient
from app.infrastructure.external_services.scraper_client import ScraperClient


class ScrapingCoordinator:
    def __init__(
        self,
        scraper_client: ScraperClient | None = None,
        llm_client: LLMClient | None = None,
    ):
        self._scraper = scraper_client or ScraperClient()
        self._llm = llm_client or LLMClient()
        self._quality_metrics: dict = {"total_scraped": 0, "approved": 0, "rejected": 0, "duplicates": 0}

    async def validate_product(self, product: dict) -> dict:
        required = ["external_id", "store", "name", "price"]
        missing = [f for f in required if not product.get(f)]
        if missing:
            self._quality_metrics["rejected"] += 1
            return {"approved": False, "reason": f"Missing fields: {missing}"}

        if not isinstance(product.get("price"), (int, float)) or product["price"] <= 0:
            self._quality_metrics["rejected"] += 1
            return {"approved": False, "reason": "Invalid price"}

        if not product.get("name") or len(product["name"].strip()) < 3:
            self._quality_metrics["rejected"] += 1
            return {"approved": False, "reason": "Name too short"}

        llm_validation = await self._llm.validate_product_data(product)
        if not llm_validation.get("valid"):
            self._quality_metrics["rejected"] += 1
            return {"approved": False, "reason": llm_validation.get("reason", "LLM validation failed")}

        self._quality_metrics["approved"] += 1
        return {"approved": True, "product": product}

    async def coordinate_scrape(self, store: str) -> dict:
        try:
            result = await self._scraper.trigger_scrape(store)
            if not result.get("success"):
                return {"success": False, "error": result.get("error", "Scrape failed")}

            products = await self._scraper.get_scraped_products(store)
            self._quality_metrics["total_scraped"] += len(products)

            seen = set()
            deduplicated = []
            for p in products:
                ext_id = p.get("external_id")
                if ext_id in seen:
                    self._quality_metrics["duplicates"] += 1
                    continue
                seen.add(ext_id)
                deduplicated.append(p)

            return {"success": True, "products": deduplicated}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def report_quality_metrics(self) -> dict:
        total = self._quality_metrics["total_scraped"]
        return {
            **self._quality_metrics,
            "approval_rate": f"{self._quality_metrics['approved'] / max(total, 1):.0%}",
            "duplicate_rate": f"{self._quality_metrics['duplicates'] / max(total, 1):.0%}",
        }
