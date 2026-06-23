from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.infrastructure.scrapers.pipeline import ScraperPipeline


class ScraperScheduler:
    def __init__(self, pipeline: ScraperPipeline):
        self._pipeline = pipeline
        self._scheduler = AsyncIOScheduler(timezone="UTC")

    def start(self):
        self._scheduler.add_job(
            self._daily_scrape,
            "cron",
            hour=2,
            minute=0,
            id="daily_scrape",
            replace_existing=True,
        )
        self._scheduler.start()

    def stop(self):
        self._scheduler.shutdown(wait=False)

    async def _daily_scrape(self):
        await self._pipeline.run_all_stores()

    async def trigger_manual(self, store: str | None = None, categories: list[str] | None = None):
        if store:
            return await self._pipeline.run_scraper(store, categories)
        return await self._pipeline.run_all_stores(categories)