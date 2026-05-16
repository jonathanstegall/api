from fastapi import Depends
from redis.asyncio import Redis
from app.core.redis import redis_client
from app.services.cache import CacheService
# Usage in routes
from fastapi import APIRouter

router = APIRouter()

async def get_redis() -> Redis:
    return redis_client.get_client()

async def get_cache(redis: Redis = Depends(get_redis)) -> CacheService:
    return CacheService(redis)

@router.get("/cache/{key}")
async def get_cached_value(key: str, redis: Redis = Depends(get_redis)):
    value = await redis.get(key)
    return {"key": key, "value": value}
