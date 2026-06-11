from datetime import datetime, timezone

from app.application.orchestrator.publication_manager import PublicationManager
from app.application.orchestrator.scraping_coordinator import ScrapingCoordinator
from app.application.orchestrator.vton_coordinator import VTONCoordinator
from app.infrastructure.external_services.llm_client import LLMClient


class PipelineOrchestrator:
    def __init__(
        self,
        scraping_coordinator: ScrapingCoordinator | None = None,
        vton_coordinator: VTONCoordinator | None = None,
        publication_manager: PublicationManager | None = None,
        llm_client: LLMClient | None = None,
    ):
        self._scraping = scraping_coordinator or ScrapingCoordinator()
        self._vton = vton_coordinator or VTONCoordinator()
        self._publication = publication_manager or PublicationManager()
        self._llm = llm_client or LLMClient()
        self._health_status: dict = {"last_pipeline_run": None, "status": "idle", "errors": []}

    async def run_pipeline(self, store: str) -> dict:
        self._health_status["status"] = "running"
        self._health_status["last_pipeline_run"] = datetime.now(timezone.utc).isoformat()
        try:
            scrape_result = await self._scraping.coordinate_scrape(store)
            if not scrape_result.get("success"):
                self._health_status["errors"].append(f"Scrape failed for {store}")
                self._health_status["status"] = "failed"
                return {"stage": "scraping", "success": False, "error": scrape_result.get("error")}

            validated = []
            for product in scrape_result.get("products", []):
                quality = await self._scraping.validate_product(product)
                if quality["approved"]:
                    approval = await self._publication.approve_product(product)
                    if approval["approved"]:
                        validated.append(product)

            decision = await self._llm.analyze(
                f"Pipeline processed {len(validated)} products from {store}. "
                f"Scraped {len(scrape_result.get('products', []))}, approved {len(validated)}. "
                f"Quality threshold met: {len(validated) / max(len(scrape_result.get('products', [])), 1):.0%}. "
                f"Should we continue publication?"
            )

            if "yes" in decision.lower():
                for product in validated:
                    await self._publication.schedule_publication(product)

            self._health_status["status"] = "completed"
            return {
                "stage": "pipeline",
                "success": True,
                "store": store,
                "scraped": len(scrape_result.get("products", [])),
                "validated": len(validated),
                "ai_decision": decision,
            }
        except Exception as e:
            self._health_status["status"] = "failed"
            self._health_status["errors"].append(str(e))
            return {"stage": "pipeline", "success": False, "error": str(e)}

    async def monitor_health(self) -> dict:
        if not self._health_status["last_pipeline_run"]:
            return {"status": "never_run", "errors": []}
        elapsed = (
            datetime.now(timezone.utc) - datetime.fromisoformat(self._health_status["last_pipeline_run"])
        ).total_seconds()
        status = "healthy" if self._health_status["status"] == "completed" else "degraded"
        return {
            "status": status,
            "last_run": self._health_status["last_pipeline_run"],
            "seconds_since_last_run": elapsed,
            "error_count": len(self._health_status["errors"]),
            "recent_errors": self._health_status["errors"][-5:],
        }

    async def get_pipeline_status(self) -> dict:
        return {
            "current_status": self._health_status["status"],
            "last_pipeline_run": self._health_status["last_pipeline_run"],
            "errors": self._health_status["errors"],
        }
