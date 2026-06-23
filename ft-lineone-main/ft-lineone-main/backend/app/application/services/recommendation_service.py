from app.domain.models.product import Product
from app.domain.models.user import User
from app.infrastructure.external_services.llm_client import LLMClient
from app.infrastructure.persistence.postgres.repositories.product_repository import (
    ProductRepository,
)


class RecommendationService:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        product_repo: ProductRepository | None = None,
    ):
        self._llm_client = llm_client or LLMClient()
        self._product_repo = product_repo or ProductRepository()

    async def get_recommendations(self, user: User, limit: int = 10) -> list[Product]:
        all_products, _ = await self._product_repo.find_all(page=1, per_page=50)
        recommended = await self._llm_client.get_recommendations(user, all_products)
        return recommended[:limit]
