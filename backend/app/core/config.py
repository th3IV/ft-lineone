from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./ft_lineone.db"
    MONGODB_URL: str = "mongodb://localhost:27017/ft_lineone"
    MONGODB_DB: str = "ft_lineone"
    
    # Replicate (VTON)
    REPLICATE_API_TOKEN: str = ""
    REPLICATE_MODEL: str = "cuuupid/idm-vton"
    
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    REDIS_URL: str = "redis://localhost:6379/0"
    GOOGLE_API_KEY: str = ""

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
