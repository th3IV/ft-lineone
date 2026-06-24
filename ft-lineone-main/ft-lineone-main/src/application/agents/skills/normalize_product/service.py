from src.application.agents.skills.normalize_product.schema import (
    NormalizeProductInput,
    NormalizeProductOutput,
)
from src.infrastructure.external_services.grok_client import GrokClient


class NormalizeProductSkill:
    def __init__(self, grok_client: GrokClient):
        self._client = grok_client
        self._skill_name = "normalize_product"

    async def execute(self, input_data: NormalizeProductInput) -> NormalizeProductOutput:
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_user_prompt(input_data.product)

        result = await self._client.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=NormalizeProductOutput,
        )
        return result

    def _get_system_prompt(self) -> str:
        return (
            "Eres un normalizador de catálogo de moda. Recibes un producto válido "
            "y debes mapearlo al schema canónico de MongoDB Atlas.\n\n"
            "Reglas de normalización:\n"
            "1. category → mapear a taxonomía estándar: [\"tops\", \"bottoms\", \"dresses\", \"outerwear\", \"shoes\", \"accessories\"]\n"
            "2. sizes → ordenar [XS,S,M,L,XL,XXL] + numéricas (36,38,40...)\n"
            "3. colors → normalizar a nombres estándar en español\n"
            "4. price → float con 2 decimales\n"
            "5. Generar slug SEO-friendly desde name (lowercase, hyphens, sin acentos)\n"
            "6. Extraer atributos: fit, material, occasion, season si están en description\n"
            "7. La imagen principal va en images[0] con is_primary=true\n\n"
            "Responde SOLO con JSON válido según el schema de salida."
        )

    def _build_user_prompt(self, product: dict) -> str:
        return f"Normaliza este producto: {product}"