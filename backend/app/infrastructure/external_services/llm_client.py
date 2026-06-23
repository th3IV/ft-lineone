import json

from langchain_core.prompts import ChatPromptTemplate

from app.domain.models.product import Product
from app.domain.models.user import User
from app.core.config import settings


class LLMClient:
    def __init__(self):
        self._available = bool(settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "demo-key")
        if self._available:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self._llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.3,
                api_key=settings.GOOGLE_API_KEY,
            )

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
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a fashion recommendation AI. Select the best products for this user. "
                "Return a JSON array of product indices (0-based) that best match the user's preferences and body type.",
            ),
            ("human", f"User profile:\n{user_context}\n\nAvailable products:\n{product_list}"),
        ])
        chain = prompt | self._llm
        response = await chain.ainvoke({})
        try:
            indices = json.loads(response.content)
            if isinstance(indices, list):
                return [products[i] for i in indices if i < len(products)]
        except (json.JSONDecodeError, IndexError):
            pass
        return products[:5]

    async def validate_product_data(self, product: dict) -> dict:
        if not self._available:
            return {"valid": True, "reason": "Validation skipped (no API key)"}
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a product data validator. Validate if the product data is complete and appropriate "
                "for an e-commerce fashion catalog. Respond with JSON: {\"valid\": bool, \"reason\": str}.",
            ),
            ("human", f"Validate this product: {json.dumps(product, default=str)}"),
        ])
        chain = prompt | self._llm
        response = await chain.ainvoke({})
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"valid": True, "reason": "Validation skipped"}

    async def generate_description(self, product: dict) -> str:
        if not self._available:
            return product.get("name", "Product description unavailable")
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a fashion copywriter. Generate a compelling product description "
                "based on the product data provided. Keep it under 200 words.",
            ),
            ("human", f"Product: {json.dumps(product, default=str)}"),
        ])
        chain = prompt | self._llm
        response = await chain.ainvoke({})
        return response.content.strip()

    async def analyze(self, context: str) -> str:
        if not self._available:
            return "yes (LLM unavailable - auto-approved)"
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a pipeline supervisor AI. Analyze the pipeline context and respond "
                "with a clear decision (yes/no) and a brief reason.",
            ),
            ("human", context),
        ])
        chain = prompt | self._llm
        response = await chain.ainvoke({})
        return response.content.strip()

