from app.domain.models.vton_result import VTONResult, VTONStatus
from app.infrastructure.external_services.vton_client import VTONClient
from app.infrastructure.persistence.postgres.repositories.product_repository import (
    ProductRepository,
)


class VTONService:
    def __init__(
        self,
        vton_client: VTONClient | None = None,
        product_repo: ProductRepository | None = None,
    ):
        self._vton_client = vton_client or VTONClient()
        self._product_repo = product_repo or ProductRepository()

    async def request_try_on(self, user_id: str, product_id: str, user_image_url: str) -> VTONResult:
        product = await self._product_repo.find_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        result = await self._vton_client.request_try_on(user_image_url, product.image_url)
        return result

    async def get_result(self, vton_id: str) -> VTONResult | None:
        return await self._vton_client.get_result(vton_id)
