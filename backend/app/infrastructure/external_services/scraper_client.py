import httpx


class ScraperClient:
    def __init__(self, base_url: str = "http://scrapers:8001"):
        self._base_url = base_url

    async def trigger_scrape(self, store: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/scrape",
                json={"store": store},
                timeout=120.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_scraped_products(self, store: str) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/products",
                params={"store": store},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else data.get("products", [])
