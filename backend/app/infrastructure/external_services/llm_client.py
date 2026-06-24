import asyncio
import json

import google.generativeai as genai

from app.domain.models.product import Product
from app.domain.models.user import User
from app.core.config import settings


class LLMClient:
    def __init__(self):
        self._available = bool(settings.GOOGLE_API_KEY)
        if self._available:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self._model = genai.GenerativeModel("gemini-2.0-flash")

    def _call_llm(self, prompt: str) -> str:
        if not self._available:
            return ""
        response = self._model.generate_content(prompt)
        return response.text.strip()

    async def _call_llm_async(self, prompt: str) -> str:
        return await asyncio.to_thread(self._call_llm, prompt)

    async def get_recommendations(self, user: User, products: list[Product]) -> list[Product]:
        if not self._available:
            return products[:5]
        user_context = (
            f"User preferences: {', '.join(user.preferences) if user.preferences else 'none'}. "
            f"Body measurements: {user.body_measurements}"
        )
        product_list = "\n".join(
            [f"- {p.name} (${p.price}, {p.store}, sizes: {p.sizes})" for p in products[:50]]
        )
        prompt = (
            "You are a fashion recommendation AI. Select the best products for this user. "
            "Return a JSON array of product indices (0-based) that best match the user's preferences and body type.\n\n"
            f"User profile:\n{user_context}\n\nAvailable products:\n{product_list}"
        )
        text = await self._call_llm_async(prompt)
        try:
            indices = json.loads(text)
            if isinstance(indices, list):
                return [products[i] for i in indices if i < len(products)]
        except (json.JSONDecodeError, IndexError):
            pass
        return products[:5]

    async def validate_product_data(self, product: dict) -> dict:
        if not self._available:
            return {"valid": True, "reason": "Validation skipped (no API key)"}
        prompt = (
            "You are a product data validator. Validate if the product data is complete and appropriate "
            "for an e-commerce fashion catalog. Respond with JSON: {\"valid\": bool, \"reason\": str}.\n\n"
            f"Validate this product: {json.dumps(product, default=str)}"
        )
        text = await self._call_llm_async(prompt)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"valid": True, "reason": "Validation skipped"}

    async def generate_description(self, product: dict) -> str:
        if not self._available:
            return product.get("name", "Product description unavailable")
        prompt = (
            "You are a fashion copywriter. Generate a compelling product description "
            "based on the product data provided. Keep it under 200 words.\n\n"
            f"Product: {json.dumps(product, default=str)}"
        )
        return await self._call_llm_async(prompt)

    async def analyze(self, context: str) -> str:
        if not self._available:
            return "yes (LLM unavailable - auto-approved)"
        prompt = (
            "You are a pipeline supervisor AI. Analyze the pipeline context and respond "
            "with a clear decision (yes/no) and a brief reason.\n\n"
            f"{context}"
        )
        return await self._call_llm_async(prompt)
