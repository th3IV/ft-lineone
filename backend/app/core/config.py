from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./ft_lineone.db"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    GOOGLE_API_KEY: str = ""
    SCRAPER_API_URL: str = "http://localhost:8001"
    VTON_API_URL: str = "http://localhost:8002"
    REACT_APP_API_URL: str = "http://localhost:8000/api/v1"

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
