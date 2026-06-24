from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Supabase (PostgreSQL)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_DB_URL: str = ""

    # MongoDB Atlas
    MONGODB_URI: str = ""

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Upstash Redis
    UPSTASH_REDIS_URL: str = ""
    UPSTASH_REDIS_TOKEN: str = ""

    # Google AI Studio (Gemini) - Fallback
    GOOGLE_AI_API_KEY: str = ""

    # xAI Grok (LLM + Imagen)
    XAI_API_KEY: str = ""

    # Hugging Face Spaces (VTON)
    HF_SPACE_URL: str = ""
    HF_TOKEN: str = ""

    # Genlook (VTON)
    GENLOOK_API_KEY: str = ""

    # Replicate (VTON / IA generativa)
    REPLICATE_API_TOKEN: str = ""

    # OpenAI (GPT) - fallback si Grok no funciona
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Rate limiting
    LLM_RATE_LIMIT_RPM: int = 30
    LLM_RATE_LIMIT_DAILY: int = 1000

    # App
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()