import asyncio
import json
import logging
import time
from typing import Type, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from src.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class TokenBucketRateLimiter:
    def __init__(self, rpm: int, daily: int):
        self._rpm = rpm
        self._daily = daily
        self._tokens = rpm
        self._daily_used = 0
        self._last_refill = time.monotonic()
        self._day_start = time.monotonic()

    async def acquire(self):
        now = time.monotonic()

        if now - self._day_start > 86400:
            self._daily_used = 0
            self._day_start = now

        if self._daily_used >= self._daily:
            wait = 86400 - (now - self._day_start)
            logger.warning("Límite diario alcanzado, esperando %.0fs", wait)
            await asyncio.sleep(wait)
            self._daily_used = 0
            self._day_start = time.monotonic()

        elapsed = now - self._last_refill
        self._tokens = min(self._rpm, self._tokens + elapsed * (self._rpm / 60))
        self._last_refill = now

        if self._tokens < 1:
            wait = (1 - self._tokens) * (60 / self._rpm)
            await asyncio.sleep(wait)
            self._tokens = 0
            self._last_refill = time.monotonic()

        self._tokens -= 1
        self._daily_used += 1

    def stats(self) -> dict:
        return {
            "tokens_remaining": round(self._tokens, 1),
            "daily_used": self._daily_used,
            "daily_limit": self._daily,
            "rpm": self._rpm,
        }


class GrokClient:
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or settings.XAI_API_KEY
        self._client = None
        self._openai_client = None
        self._fallback_client = None
        self._available = bool(self._api_key and self._api_key != "demo-key")

        if self._available:
            try:
                self._client = AsyncOpenAI(
                    base_url="https://api.x.ai/v1",
                    api_key=self._api_key,
                )
            except Exception:
                self._available = False

        self._init_openai()
        self._init_gemini()

        self._rate_limiter = TokenBucketRateLimiter(
            rpm=settings.LLM_RATE_LIMIT_RPM,
            daily=settings.LLM_RATE_LIMIT_DAILY,
        )

    def _init_openai(self):
        openai_key = settings.OPENAI_API_KEY
        if openai_key:
            try:
                self._openai_client = AsyncOpenAI(api_key=openai_key)
                self._openai_model = settings.OPENAI_MODEL
                logger.info("Fallback: OpenAI (%s) configurado", self._openai_model)
            except Exception as e:
                logger.warning("OpenAI no disponible: %s", e)

    def _init_gemini(self):
        gemini_key = settings.GOOGLE_AI_API_KEY
        if gemini_key:
            try:
                from google import genai as google_genai
                self._fallback_client = google_genai.Client(api_key=gemini_key)
                self._fallback_model = "gemini-2.0-flash"
                logger.info("Fallback: Google AI (Gemini 2.0 Flash) configurado")
            except Exception as e:
                logger.warning("Gemini no disponible: %s", e)

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
        temperature: float = 0.1,
        max_output_tokens: int = 2048,
    ) -> T:
        await self._rate_limiter.acquire()

        if self._available:
            try:
                return await self._generate_structured_grok(
                    system_prompt, user_prompt, response_schema, temperature, max_output_tokens
                )
            except Exception as e:
                logger.warning("Grok falló, intentando OpenAI: %s", e)

        if self._openai_client:
            try:
                return await self._generate_structured_openai(
                    system_prompt, user_prompt, response_schema, temperature, max_output_tokens
                )
            except Exception as e:
                logger.warning("OpenAI falló, intentando Gemini: %s", e)

        if self._fallback_client:
            return await self._generate_structured_gemini(
                system_prompt, user_prompt, response_schema, temperature, max_output_tokens
            )

        logger.warning("Sin LLM disponible, devolviendo schema vacío")
        try:
            return response_schema()
        except Exception:
            return response_schema.model_construct()

    async def _generate_structured_grok(
        self, system_prompt: str, user_prompt: str, response_schema: Type[T],
        temperature: float, max_output_tokens: int,
    ) -> T:
        schema = response_schema.model_json_schema()
        schema_str = json.dumps(schema, ensure_ascii=False)
        full_prompt = f"{system_prompt}\n\nResponde ÚNICAMENTE con JSON válido que cumpla este schema:\n{schema_str}\n\n{user_prompt}"

        response = await self._client.chat.completions.create(
            model="grok-4.3",
            messages=[{"role": "system", "content": full_prompt}],
            temperature=temperature,
            max_tokens=max_output_tokens,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content)
        return response_schema(**parsed)

    async def _generate_structured_openai(
        self, system_prompt: str, user_prompt: str, response_schema: Type[T],
        temperature: float, max_output_tokens: int,
    ) -> T:
        schema = response_schema.model_json_schema()
        schema_str = json.dumps(schema, ensure_ascii=False)
        full_prompt = f"{system_prompt}\n\nResponde ÚNICAMENTE con JSON válido que cumpla este schema:\n{schema_str}\n\n{user_prompt}"

        response = await self._openai_client.chat.completions.create(
            model=self._openai_model,
            messages=[{"role": "system", "content": full_prompt}],
            temperature=temperature,
            max_tokens=max_output_tokens,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content)
        return response_schema(**parsed)

    async def _generate_structured_gemini(
        self, system_prompt: str, user_prompt: str, response_schema: Type[T],
        temperature: float, max_output_tokens: int,
    ) -> T:
        from google.genai import types

        schema = response_schema.model_json_schema()
        schema_str = json.dumps(schema, ensure_ascii=False)
        full_prompt = f"{system_prompt}\n\nResponde ÚNICAMENTE con JSON válido que cumpla este schema:\n{schema_str}\n\n{user_prompt}"

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
        )
        try:
            response = await self._fallback_client.aio.models.generate_content(
                model=self._fallback_model,
                contents=full_prompt,
                config=config,
            )
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning("Gemini cuota excedida")
                try:
                    return response_schema()
                except Exception:
                    return response_schema.model_construct()
            raise

        parsed = json.loads(response.text)
        return response_schema(**parsed)

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_output_tokens: int = 1024,
    ) -> str:
        await self._rate_limiter.acquire()

        if self._available:
            try:
                return await self._generate_text_grok(prompt, temperature, max_output_tokens)
            except Exception as e:
                logger.warning("Grok text falló, intentando OpenAI: %s", e)

        if self._openai_client:
            try:
                return await self._generate_text_openai(prompt, temperature, max_output_tokens)
            except Exception as e:
                logger.warning("OpenAI text falló, intentando Gemini: %s", e)

        if self._fallback_client:
            return await self._generate_text_gemini(prompt, temperature, max_output_tokens)

        return "LLM no disponible"

    async def _generate_text_grok(self, prompt: str, temperature: float, max_output_tokens: int) -> str:
        response = await self._client.chat.completions.create(
            model="grok-4.3",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_output_tokens,
        )
        return response.choices[0].message.content.strip()

    async def _generate_text_openai(self, prompt: str, temperature: float, max_output_tokens: int) -> str:
        response = await self._openai_client.chat.completions.create(
            model=self._openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_output_tokens,
        )
        return response.choices[0].message.content.strip()

    async def _generate_text_gemini(self, prompt: str, temperature: float, max_output_tokens: int) -> str:
        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        try:
            response = await self._fallback_client.aio.models.generate_content(
                model=self._fallback_model,
                contents=prompt,
                config=config,
            )
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning("Gemini cuota excedida para texto")
                return "Gemini cuota excedida"
            raise

        return response.text.strip()

    async def generate_image(
        self,
        prompt: str,
        image_urls: list[str] | None = None,
        aspect_ratio: str = "3:4",
        resolution: str = "2k",
        image_format: str = "url",
    ) -> dict:
        if self._available:
            try:
                response = await self._client.images.generate(
                    model="grok-imagine-image",
                    prompt=prompt,
                    n=1,
                    quality="standard",
                    size="1024x1365" if aspect_ratio == "3:4" else "1024x1024",
                )
                return {
                    "url": response.data[0].url,
                    "revised_prompt": response.data[0].revised_prompt if hasattr(response.data[0], "revised_prompt") else prompt,
                }
            except Exception as e:
                logger.warning("Grok image falló: %s", e)

        if self._openai_client:
            try:
                response = await self._openai_client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    n=1,
                    size="1024x1792" if aspect_ratio == "9:16" else "1024x1024",
                )
                return {"url": response.data[0].url, "revised_prompt": prompt}
            except Exception as e:
                logger.warning("OpenAI image falló: %s", e)

        raise RuntimeError("No hay servicio de generación de imágenes disponible")
