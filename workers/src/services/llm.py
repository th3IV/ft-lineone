"""LLM Recommendation service using Cloudflare Workers AI."""

import json
from typing import Optional


class LLMService:
    """LLM service using Cloudflare Workers AI (@cf/meta/llama-3.3-70b-instruct)."""

    def __init__(self, env):
        self.env = env
        self.ai = env.AI  # Workers AI binding

    async def get_recommendations(
        self,
        user_preferences: dict,
        available_products: list[dict],
        query: Optional[str] = None,
    ) -> list[dict]:
        """Get personalized product recommendations using LLM.

        Args:
            user_preferences: User's style preferences and history
            available_products: List of available products to recommend from
            query: Optional natural language query for recommendations

        Returns:
            List of recommended product IDs with reasoning
        """
        try:
            # Build the prompt
            prompt = self._build_recommendation_prompt(
                user_preferences, available_products, query
            )

            # Call Workers AI LLM
            result = await self.ai.run(
                "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
                {
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Eres un asesor de moda experto para TheLineOne, una plataforma de "
                                "moda en Chile. Recomienda productos basándote en las preferencias "
                                "del usuario, tendencias actuales y compatibilidad de estilos. "
                                "Responde SOLO con un JSON válido que contenga los IDs de productos "
                                "recomendados con una breve razón para cada uno."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 1024,
                    "temperature": 0.7,
                },
            )

            # Parse the response
            if result and "response" in result:
                return self._parse_recommendations(result["response"], available_products)
            else:
                return self._fallback_recommendations(available_products)

        except Exception as e:
            # Fallback to simple recommendations if LLM fails
            return self._fallback_recommendations(available_products)

    async def get_style_advice(
        self,
        product_name: str,
        product_category: str,
        user_question: str,
    ) -> str:
        """Get style advice for a specific product."""
        try:
            prompt = (
                f"Producto: {product_name} (categoría: {product_category})\n"
                f"Pregunta del usuario: {user_question}\n\n"
                "Proporciona un consejo de estilo conciso y útil en español."
            )

            result = await self.ai.run(
                "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
                {
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Eres un asesor de moda experto. Proporciona consejos prácticos "
                                "y específicos sobre combinaciones, colores y tendencias."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 512,
                    "temperature": 0.7,
                },
            )

            if result and "response" in result:
                return result["response"]
            else:
                return "Lo siento, no pude generar un consejo en este momento."

        except Exception:
            return "Servicio de recomendaciones no disponible temporalmente."

    def _build_recommendation_prompt(
        self,
        user_preferences: dict,
        available_products: list[dict],
        query: Optional[str] = None,
    ) -> str:
        """Build the recommendation prompt."""
        prompt_parts = []

        if query:
            prompt_parts.append(f"Solicitud del usuario: {query}")

        if user_preferences.get("gender"):
            prompt_parts.append(f"Género: {user_preferences['gender']}")

        if user_preferences.get("clothing_type"):
            prompt_parts.append(f"Tipo de ropa preferida: {', '.join(user_preferences['clothing_type'])}")

        if user_preferences.get("budget"):
            prompt_parts.append(f"Presupuesto: ${user_preferences['budget']} CLP")

        # Include available products
        products_text = json.dumps(
            [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "store": p["store"],
                    "price": p["price"],
                    "category": p.get("category", ""),
                    "colors": p.get("colors", []),
                }
                for p in available_products[:20]  # Limit to 20 products
            ],
            ensure_ascii=False,
            indent=2,
        )

        prompt_parts.append(f"\nProductos disponibles:\n{products_text}")
        prompt_parts.append(
            "\nResponde con un JSON que contenga una lista de objetos con 'product_id' y 'reason'."
        )

        return "\n".join(prompt_parts)

    def _parse_recommendations(
        self, llm_response: str, available_products: list[dict]
    ) -> list[dict]:
        """Parse LLM response into structured recommendations."""
        try:
            # Try to extract JSON from the response
            # The LLM might wrap it in markdown code blocks
            if "```json" in llm_response:
                json_str = llm_response.split("```json")[1].split("```")[0].strip()
            elif "```" in llm_response:
                json_str = llm_response.split("```")[1].split("```")[0].strip()
            else:
                json_str = llm_response.strip()

            data = json.loads(json_str)

            if isinstance(data, list):
                recommendations = []
                product_ids = {p["id"] for p in available_products}

                for item in data:
                    if isinstance(item, dict) and "product_id" in item:
                        if item["product_id"] in product_ids:
                            recommendations.append(item)
                return recommendations

        except (json.JSONDecodeError, IndexError):
            pass

        return self._fallback_recommendations(available_products)

    def _fallback_recommendations(self, available_products: list[dict]) -> list[dict]:
        """Simple fallback recommendations based on popularity/price."""
        # Sort by price (mid-range products tend to be more popular)
        sorted_products = sorted(
            available_products, key=lambda p: abs(p.get("price", 0) - 30000)
        )

        return [
            {"product_id": p["id"], "reason": "Producto popular"}
            for p in sorted_products[:5]
        ]
