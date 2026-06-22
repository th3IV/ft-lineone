import asyncio

from app.celery_app import celery_app
from app.application.orchestrator.scraping_coordinator import ScrapingCoordinator


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    return loop.run_until_complete(coro)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def scrape_store(self, store: str):
    coordinator = ScrapingCoordinator()
    result = _run_async(coordinator.coordinate_scrape(store))
    if not result.get("success"):
        raise self.retry(exc=Exception(result.get("error", "Unknown error")))
    return result


@celery_app.task(bind=True)
def scrape_all_stores(self, stores: list[str] | None = None):
    if stores is None:
        stores = ["falabella", "ripley", "paris", "maui", "zara"]
    results = []
    for store in stores:
        try:
            result = scrape_store.delay(store)
            results.append({"store": store, "task_id": result.id})
        except Exception as e:
            results.append({"store": store, "error": str(e)})
    return {"triggered": results}
