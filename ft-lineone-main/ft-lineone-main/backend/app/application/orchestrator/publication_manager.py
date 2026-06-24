from datetime import datetime, timezone
from typing import Any

from app.domain.models.product import Product
from app.infrastructure.external_services.llm_client import LLMClient


class PublicationManager:
    def __init__(self, llm_client: LLMClient | None = None):
        self._llm = llm_client or LLMClient()
        self._scheduled: dict[str, dict[str, Any]] = {}
        self._published: dict[str, dict[str, Any]] = {}

    async def approve_product(self, product: Product | dict) -> dict:
        product_dict = product if isinstance(product, dict) else product.model_dump()
        has_description = bool(product_dict.get("description"))
        has_image = bool(product_dict.get("image_url"))
        has_valid_price = isinstance(product_dict.get("price"), (int, float)) and product_dict["price"] > 0

        if not all([has_description, has_image, has_valid_price]):
            return {
                "approved": False,
                "reason": "Missing description, image, or valid price",
            }

        llm_approval = await self._llm.validate_product_data(product_dict)
        return {
            "approved": llm_approval.get("valid", False),
            "reason": llm_approval.get("reason", "LLM approval check"),
        }

    async def schedule_publication(self, product: Product | dict, publish_at: datetime | None = None) -> dict:
        product_dict = product if isinstance(product, dict) else product.model_dump()
        product_id = product_dict.get("id") or product_dict.get("external_id")
        schedule_time = publish_at or datetime.now(timezone.utc)
        self._scheduled[product_id] = {
            "product": product_dict,
            "scheduled_at": schedule_time.isoformat(),
            "published": False,
        }
        return {
            "product_id": product_id,
            "scheduled_at": schedule_time.isoformat(),
            "status": "scheduled",
        }

    async def unpublish(self, product_id: str) -> dict:
        if product_id in self._published:
            del self._published[product_id]
        if product_id in self._scheduled:
            self._scheduled[product_id]["published"] = False
        return {"product_id": product_id, "status": "unpublished"}
