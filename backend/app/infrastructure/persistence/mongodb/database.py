from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDBClient:
    def __init__(self):
        self._client = AsyncIOMotorClient(settings.MONGODB_URL)
        self._db = self._client.get_database(settings.MONGODB_DB)

    def get_database(self):
        return self._db

# Singleton instance
mongodb_client = MongoDBClient()
