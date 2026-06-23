from src.application.agents.skills.recommend_products.schema import (
    RecommendProductsInput,
    RecommendProductsOutput,
    UserProfile,
    ProductSummary,
)
from src.infrastructure.external_services.grok_client import GrokClient


class RecommendProductsSkill:
    def __init__(self, grok_client: GrokClient):
        self._client = grok_client

    async def execute(self, input_data: RecommendProductsInput) -> RecommendProductsOutput:
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_user_prompt(input_data)

        result = await self._client.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=RecommendProductsOutput,
            temperature=0.3,
            max_output_tokens=2048,
        )
        return result

    def _get_system_prompt(self) -> str:
        return (
            "Eres un asesor de moda experto. Dado el perfil del usuario y un catálogo de productos, "
            "selecciona los TOP productos que mejor encajen.\n\n"
            "Criterios de recomendación:\n"
            "1. Match de categoría/subcategoría con preferencias del usuario\n"
            "2. Tallas disponibles que coincidan con medidas del usuario\n"
            "3. Colores que favorezcan según tono de piel/preferencias\n"
            "4. Precio dentro del rango del usuario (si especificado)\n"
            "5. Estilo coherente con historial de compras/likes\n"
            "6. Diversidad: no repetir misma subcategoría más de 2 veces\n\n"
            "Responde SOLO con JSON válido según el schema de salida."
        )

    def _build_user_prompt(self, input_data: RecommendProductsInput) -> str:
        user = input_data.user_profile
        products = input_data.products[:50]  # Limitar para token limit

        user_str = (
            f"USER PROFILE:\n"
            f"- ID: {user.user_id}\n"
            f"- Medidas: {user.body_measurements.model_dump(exclude_none=True)}\n"
            f"- Preferencias estilo: {', '.join(user.preferences) if user.preferences else 'ninguna'}\n"
            f"- Colores favoritos: {', '.join(user.favorite_colors) if user.favorite_colors else 'ninguno'}\n"
            f"- Rango precio: {user.price_range if user.price_range else 'sin límite'}\n"
            f"- Notas estilo: {user.style_notes if user.style_notes else 'ninguna'}\n\n"
        )

        products_str = "AVAILABLE PRODUCTS:\n"
        for i, p in enumerate(products):
            colors = ", ".join([c.name for c in p.colors])
            sizes = ", ".join(p.sizes)
            attrs = []
            if p.attributes.fit:
                attrs.append(f"fit:{p.attributes.fit}")
            if p.attributes.material:
                attrs.append(f"material:{p.attributes.material}")
            if p.attributes.occasion:
                attrs.append(f"occasion:{p.attributes.occasion}")
            attr_str = f" ({', '.join(attrs)})" if attrs else ""

            products_str += (
                f"{i}. [{p.external_id}] {p.name} - {p.price} {p.currency} "
                f"({p.category}/{p.subcategory}) | Sizes: {sizes} | Colors: {colors}{attr_str}\n"
            )

        return f"{user_str}{products_str}\nSelecciona los TOP {input_data.limit} productos con score y razón."