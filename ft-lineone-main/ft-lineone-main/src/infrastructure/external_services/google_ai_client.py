import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from pydantic import BaseModel
from typing import Type, TypeVar
import json
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GoogleAIClient:
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or settings.GOOGLE_AI_API_KEY
        genai.configure(api_key=self._api_key)
        self._model = genai.GenerativeModel("gemini-1.5-flash")

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
        temperature: float = 0.1,
        max_output_tokens: int = 2048,
    ) -> T:
        schema = response_schema.model_json_schema()
        schema_str = json.dumps(schema, ensure_ascii=False)

        full_prompt = f"{system_prompt}\n\nResponde ÚNICAMENTE con JSON válido que cumpla este schema:\n{schema_str}\n\n{user_prompt}"

        config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
        )

        try:
            response = await self._model.generate_content_async(full_prompt, generation_config=config)
            parsed = json.loads(response.text)
            return response_schema(**parsed)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from Gemini: %s | Raw: %s", e, response.text[:500])
            raise ValueError(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.error("Gemini generation failed: %s", e)
            raise

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_output_tokens: int = 1024,
    ) -> str:
        config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        response = await self._model.generate_content_async(prompt, generation_config=config)
        return response.text.strip()