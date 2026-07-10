# nemesis/storage/mongo.py

from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from nemesis.core.config import settings
from nemesis.storage.interfaces import DocumentStore
from nemesis.observability.telemetry import logger, tracer

class MongoStore(DocumentStore):
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.collection = None

    async def connect(self):
        if settings.database_mongo_url and "ROTATE" not in settings.database_mongo_url:
            try:
                self.client = AsyncIOMotorClient(settings.database_mongo_url, serverSelectionTimeoutMS=5000)
                self.db = self.client.nemesis
                self.collection = self.db.traces
                # Test connection
                await self.client.server_info()
                logger.info("MongoDB connection established.")
            except Exception as e:
                logger.error(f"MongoDB connection failed: {e}")
                self.client = None
        else:
            logger.warning("MongoDB URL not configured or contains placeholder. Operating in memory-only mode for documents.")

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    @tracer.start_as_current_span("mongo.save_trace")
    async def save_trace(self, trace_id: str, data: Dict[str, Any]):
        if not self.collection: return
        try:
            await self.collection.update_one(
                {"_id": trace_id},
                {"$set": {"data": data}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Failed to save trace to Mongo: {e}")

    @tracer.start_as_current_span("mongo.get_trace")
    async def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        if not self.collection: return None
        try:
            doc = await self.collection.find_one({"_id": trace_id})
            return doc.get("data") if doc else None
        except Exception as e:
            logger.error(f"Failed to retrieve trace from Mongo: {e}")
            return None
