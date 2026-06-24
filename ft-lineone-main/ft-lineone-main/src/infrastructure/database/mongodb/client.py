from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from src.core.config import settings
from src.infrastructure.database.mongodb.models import ProductDocument


class MongoDBClient:
    _client: AsyncIOMotorClient | None = None
    _db = None

    @classmethod
    async def connect(cls):
        if cls._client is None:
            cls._client = AsyncIOMotorClient(settings.MONGODB_URI)
            cls._db = cls._client.get_default_database()
            await init_beanie(
                database=cls._db,
                document_models=[ProductDocument],
            )

    @classmethod
    async def close(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None

    @classmethod
    def get_db(cls):
        return cls._db