from enum import Enum
from typing import Optional
from src.application.agents.skills.recommend_products.service import RecommendProductsSkill
from src.application.agents.skills.recommend_products.schema import RecommendProductsInput, UserProfile, ProductSummary
from src.application.agents.skills.virtual_try_on.service import VTONSkill
from src.application.agents.skills.virtual_try_on.schema import VTONSkillInput
from src.infrastructure.database.mongodb.repositories import MongoProductRepository
from src.infrastructure.external_services.grok_client import GrokClient


class IntentType(str, Enum):
    RECOMMEND = "recommend"
    VIRTUAL_TRY_ON = "virtual_try_on"
    CHAT = "chat"
    UNKNOWN = "unknown"


class FashionAdvisorAgent:
    def __init__(
        self,
        grok_client: GrokClient,
        recommend_skill: RecommendProductsSkill,
        vton_skill: VTONSkill,
        product_repo: MongoProductRepository,
    ):
        self._llm = grok_client
        self._recommend_skill = recommend_skill
        self._vton_skill = vton_skill
        self._product_repo = product_repo

    async def process_message(
        self,
        user_id: str,
        message: str,
        user_profile: UserProfile,
        context: dict | None = None,
    ) -> dict:
        intent = await self._classify_intent(message, context)

        if intent == IntentType.RECOMMEND:
            return await self._handle_recommend(user_id, user_profile, context)
        elif intent == IntentType.VIRTUAL_TRY_ON:
            return await self._handle_vton(message, user_id, user_profile, context)
        else:
            return await self._handle_chat(message, user_profile, context)

    async def _classify_intent(self, message: str, context: dict | None) -> IntentType:
        prompt = (
            "Clasifica la intención del usuario en una de estas categorías:\n"
            "1. recommend - Quiere recomendaciones de ropa/outfits\n"
            "2. virtual_try_on - Quiere probarse una prenda virtualmente\n"
            "3. chat - Conversación general, dudas, saludos\n\n"
            f"Mensaje: \"{message}\"\n"
            f"Contexto: {context or 'ninguno'}\n\n"
            "Responde SOLO con: recommend, virtual_try_on, o chat"
        )
        try:
            response = await self._llm.generate_text(prompt, temperature=0.1, max_output_tokens=50)
            return IntentType(response.strip().lower())
        except Exception:
            return IntentType.UNKNOWN

    async def _handle_recommend(
        self,
        user_id: str,
        user_profile: UserProfile,
        context: dict | None,
    ) -> dict:
        products, _ = await self._product_repo.find_all(page=1, per_page=50)
        product_summaries = [self._to_summary(p) for p in products]

        input_data = RecommendProductsInput(
            user_profile=user_profile,
            products=product_summaries,
            limit=10,
        )
        result = await self._recommend_skill.execute(input_data)

        return {
            "type": "recommendations",
            "message": f"Encontré {len(result.recommendations)} recomendaciones para ti:",
            "data": {
                "recommendations": [
                    {
                        "product_id": r.product_id,
                        "score": r.score,
                        "reason": r.reason,
                        "matched_attributes": r.matched_attributes,
                    }
                    for r in result.recommendations
                ]
            },
        }

    async def _handle_vton(
        self,
        message: str,
        user_id: str,
        user_profile: UserProfile,
        context: dict | None,
    ) -> dict:
        product_id = context.get("product_id") if context else None
        product_image_url = context.get("product_image_url") if context else None
        user_image_url = context.get("user_image_url") if context else None

        if not product_id or not product_image_url or not user_image_url:
            return {
                "type": "error",
                "message": "Para probarte una prenda necesito: tu foto, la foto de la prenda y el ID del producto.",
                "missing": {
                    "product_id": not product_id,
                    "product_image_url": not product_image_url,
                    "user_image_url": not user_image_url,
                },
            }

        input_data = VTONSkillInput(
            user_id=user_id,
            user_image_url=user_image_url,
            product_id=product_id,
            product_image_url=product_image_url,
        )
        result = await self._vton_skill.execute(input_data)

        return {
            "type": "vton_result",
            "message": "Tu prueba virtual está procesándose..." if result.status == "processing" else "¡Prueba virtual completada!",
            "data": {
                "job_id": result.job_id,
                "status": result.status,
                "result_url": str(result.result_url) if result.result_url else None,
                "error": result.error,
            },
        }

    async def _handle_chat(
        self,
        message: str,
        user_profile: UserProfile,
        context: dict | None,
    ) -> dict:
        prompt = (
            f"Eres un asesor de moda amable. Usuario: {user_profile.user_id}. "
            f"Preferencias: {', '.join(user_profile.preferences) if user_profile.preferences else 'ninguna'}.\n"
            f"Responde de forma natural y útil a: \"{message}\""
        )
        response = await self._llm.generate_text(prompt, temperature=0.5, max_output_tokens=500)
        return {"type": "chat", "message": response, "data": {}}

    def _to_summary(self, product) -> ProductSummary:
        from src.application.agents.skills.recommend_products.schema import (
            ProductColor, ProductImage, ProductAttributes
        )
        return ProductSummary(
            external_id=product.external_id,
            store=product.store,
            slug=product.slug,
            name=product.name,
            description=product.description,
            price=product.price,
            currency=product.currency,
            category=product.category,
            subcategory=product.subcategory,
            sizes=product.sizes,
            colors=[ProductColor(name=c.name) for c in product.colors],
            images=[ProductImage(url=img.url, width=img.width, height=img.height, is_primary=img.is_primary) for img in product.images],
            attributes=ProductAttributes(
                fit=product.attributes.fit,
                material=product.attributes.material,
                occasion=product.attributes.occasion,
                season=product.attributes.season,
            ),
        )