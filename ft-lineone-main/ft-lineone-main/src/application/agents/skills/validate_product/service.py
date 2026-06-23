from src.application.agents.skills.validate_product.schema import (
    ValidateProductInput,
    ValidateProductOutput,
    RawProduct,
)
from src.infrastructure.external_services.grok_client import GrokClient


class ValidateProductSkill:
    def __init__(self, grok_client: GrokClient):
        self._client = grok_client
        self._skill_name = "validate_product_data"

    async def execute(self, input_data: ValidateProductInput) -> ValidateProductOutput:
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_user_prompt(input_data.product)

        result = await self._client.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=ValidateProductOutput,
        )
        return result

    def _get_system_prompt(self) -> str:
        return (
            "Eres un validador de datos de e-commerce de moda. Recibes un producto crudo scrapeado "
            "y debes determinar si es válido para guardar en catálogo.\n\n"
            "Criterios de validación:\n"
            "1. Campos obligatorios: external_id, store, name, price, image_url\n"
            "2. Price > 0 y numérico\n"
            "3. Name length >= 3 caracteres\n"
            "4. image_url es URL válida (http/https)\n"
            "5. Store ∈ {\"zara\", \"hm\", \"falabella\", \"ripley\", \"paris\", \"maui\"}\n"
            "6. No contenido inapropiado, duplicados obvios, datos corruptos\n\n"
            "Responde SOLO con JSON válido según el schema de salida."
        )

    def _build_user_prompt(self, product: RawProduct) -> str:
        return f"Valida este producto: {product.model_dump_json()}"