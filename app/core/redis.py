from redis.asyncio import Redis, ConnectionPool
from contextlib import asynccontextmanager
import os

from app.core.config import settings

# Redis credentials
REDIS_URL = settings.REDIS_URL

class RedisClient:
    def __init__(self):
        self.pool: ConnectionPool = None
        self.client: Redis = None

    async def connect(self):
        self.pool = ConnectionPool.from_url(
            os.getenv("REDIS_URL", REDIS_URL),
            max_connections=50,
            decode_responses=True
        )
        self.client = Redis(connection_pool=self.pool)

    async def disconnect(self):
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()

    def get_client(self) -> Redis:
        return self.client

redis_client = RedisClient()

# Lifespan context manager
@asynccontextmanager
async def lifespan(app):
    await redis_client.connect()
    yield
    await redis_client.disconnect()
