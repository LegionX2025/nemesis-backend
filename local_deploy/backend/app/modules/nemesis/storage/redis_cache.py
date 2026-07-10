# nemesis/storage/redis_cache.py

import json
from typing import Optional
import redis.asyncio as redis
from nemesis.core.config import settings
from nemesis.storage.interfaces import CacheStore
from nemesis.observability.telemetry import logger, tracer

class RedisStore(CacheStore):
    def __init__(self):
        self.pool: Optional[redis.Redis] = None

    async def connect(self):
        if settings.redis_url and "ROTATE" not in settings.redis_url:
            try:
                self.pool = redis.from_url(settings.redis_url, decode_responses=True)
                await self.pool.ping()
                logger.info("Redis connection established.")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self.pool = None
        else:
            logger.warning("Redis URL not configured. Cache operations will be ignored.")

    async def close(self):
        if self.pool:
            await self.pool.aclose()
            logger.info("Redis connection closed.")

    @tracer.start_as_current_span("redis.set")
    async def set(self, key: str, value: str, ttl_seconds: int = 3600):
        if not self.pool: return
        try:
            await self.pool.set(key, value, ex=ttl_seconds)
        except Exception as e:
            logger.error(f"Redis set failed: {e}")

    @tracer.start_as_current_span("redis.get")
    async def get(self, key: str) -> Optional[str]:
        if not self.pool: return None
        try:
            return await self.pool.get(key)
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return None
