from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./ft_lineone.db"
    MONGODB_URL: str = "mongodb://localhost:27017/ft_lineone"
    MONGODB_DB: str = "ft_lineone"
    
    # Cloudflare R2 Storage
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = "ft-lineone-media"
    R2_ENDPOINT: str = ""
    R2_PUBLIC_URL: str = ""
    
    # Replicate (VTON)
    REPLICATE_API_TOKEN: str = ""
    REPLICATE_MODEL: str = "cuuupid/idm-vton"
    
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    OPENAI_API_KEY: str = ""

    @property

    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
